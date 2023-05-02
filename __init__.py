from mycroft import MycroftSkill, intent_file_handler
from .database import Database
from escpos.connections import getNetworkPrinter
from .category_sorter import sort_items
from Levenshtein import distance
from os.path import dirname, join
import gkeepapi
import json

LIST_NAME = "shopping"

class SimpleShoppingList(MycroftSkill):
    def __init__(self):
        MycroftSkill.__init__(self)
        self.db = Database()
        self.keep = None
        json_path = join(dirname(__file__),"auth.txt")
        with open(json_path, 'r') as json_file:
            self.auth = json.load(json_file)
        self._init_keep()
        try:
            self.sync_keep_list()
        except:
            self.keep = None

    def _init_keep(self):
        try:
            self.keep = gkeepapi.Keep()
            self.keep.resume(self.auth["email"],self.auth["token"])
        except:
            self.keep = None


    def _ensure_list_exists(self):
        """If the list does not exits, create it."""
        if not self.db.list_exists(LIST_NAME):
            self.db.add_list(LIST_NAME)

    @intent_file_handler('add.intent')
    def handle_add(self, message):
        self._ensure_list_exists()
        self.sync_keep_list()
        item = message.data.get("item")
        data = {"item":item}
        if item:
            if self.db.item_exists("shopping",item):
                self.speak_dialog('already_exists',data)
            else:
                self.db.add_item("shopping",item)
                self.sync_keep_list()
                self.speak_dialog('add',data)

    @intent_file_handler('read.intent')
    def handle_read(self, message):
        data = {}
        self._ensure_list_exists()
        self.sync_keep_list()
        if self.db.list_empty("shopping"):
            self.speak_dialog('list_is_empty')
        else:
            data['items'] = self.string(self.db.read_items("shopping"))
            self.speak_dialog('read_items', data)

    @intent_file_handler('count.intent')
    def handle_count(self, message):
        data = {}
        self._ensure_list_exists()
        self.sync_keep_list()
        if self.db.list_empty("shopping"):
            self.speak_dialog('list_is_empty')
        else:
            count = len(self.db.read_items("shopping"))
            if count == 1:
                data['count'] = f"is {count} item"
                data['short_count'] = f"{count} item"
            else:
                data['count'] = f"are {count} items"
                data['short_count'] = f"{count} items"
            self.speak_dialog('count', data)

    @intent_file_handler('print.intent')
    def handle_print(self, message):
        self._ensure_list_exists()
        self.sync_keep_list()
        if self.db.list_empty("shopping"):
            self.speak_dialog('list_is_empty')
        else:
            entries = self.db.read_items("shopping")
            # Sort the entries according to where they appear in the store
            entries = sort_items(entries)
            printer = getNetworkPrinter()(host='printer', port=9100)
            for entry in entries:
                printer.text(entry)
                printer.lf()
                printer.cr()
            self.speak_dialog('print_items')

    @intent_file_handler('delete_last.intent')
    def handle_delete_last(self, message):
        self._ensure_list_exists()
        if self.db.list_empty("shopping"):
            self.speak_dialog('list_is_empty')
        else:
            item = self.db.read_items("shopping")[-1]
            self.delete_item(item)
            self.sync_delete(item)


    @intent_file_handler('delete.intent')
    def handle_delete(self, message):
        item = message.data.get("item")
        self._ensure_list_exists()
        if self.db.list_empty("shopping"):
            self.speak_dialog('list_is_empty')
        elif item:
            if not self.db.item_exists("shopping",item):
                data = {"item":item}
                self.speak_dialog('not_found',data)
                # Find the item in the database that most closely match the input
                min_dist = float('inf')
                min_word = None
                entries = self.db.read_items("shopping")
                for entry in entries:
                    dist = distance(item,entry)
                    if dist < min_dist:
                        min_dist = dist
                        min_word = entry
                data["item"] = min_word
                resp = self.ask_yesno("did_you_mean",data)
                if resp == "yes":
                    self.db.del_item("shopping", min_word)
                    self.speak_dialog("deleted", data)
            else:
                self.delete_item(item)
            self.sync_keep_list()


    def delete_item(self, item: str):
        if self.confirm_deletion(item):
            self.db.del_item("shopping", item)
            self.sync_delete(item)
            self.speak_dialog('deleted', {"item":item})
            self.sync_keep_list()



    def confirm_deletion(self, element):
        """ Make sure the user really wants to delete 'element' """
        resp = self.ask_yesno('confirm.deletion', data={'element': element})
        if resp == 'yes':
            return True
        else:
            self.speak_dialog('cancelled')
        return False


    @intent_file_handler('clear_list.intent')
    def handle_clear_list(self, message):
        self._ensure_list_exists()
        if self.db.list_empty("shopping"):
            self.speak_dialog('list_is_empty')
        else:
            self.clear_list()


    def clear_list(self):
        """Clear the shopping list"""
        resp = self.ask_yesno('confirm.clear')
        if resp == 'yes':
            self.db.del_list("shopping")
            if not self.keep:
                self._init_keep()
            self.keep.sync()
            shoppinglist = next(self.keep.find(query="shoppinglist", archived=False, trashed=False), None)
            for item in shoppinglist.items:
                item.delete()
            self.keep.sync()
            self.speak_dialog('list_is_empty')
        else:
            self.speak_dialog('cancelled')
        return False

    def find_item(self, list, name: str):
        """Find an item in the keep list."""
        for item in list.items:
            if item.text == name:
                return item
        return None

    def sync_delete(self, item: str):
        if not self.keep:
            self._init_keep()
        self.keep.sync()
        shoppinglist = next(self.keep.find(query="shoppinglist", archived=False, trashed=False), None)
        remote_item = self.find_item(shoppinglist,item)
        remote_item.delete()
        self.keep.sync()

    def sync_keep_list(self):
        """Sync the local database and the keep list."""
        if not self.keep:
            self._init_keep()
        self.keep.sync()
        shoppinglist = next(self.keep.find(query="shoppinglist", archived=False, trashed=False), None)
        if not shoppinglist:
            shoppinglist = self.keep.createList("shoppinglist")
        # Make sure all items on local list are on keep list
        entries = self.db.read_items("shopping")
        if entries:
            # Sort the entries according to where they appear in the store
            entries = sort_items(entries)
            index = len(entries)+1
            for entry in entries:
                remote_entry = self.find_item(shoppinglist,entry)
                if not remote_entry:
                    remote_entry = shoppinglist.add(entry, False, gkeepapi.node.NewListItemPlacementValue.Bottom)
                remote_entry.sort = index
                index -= 1
        # Delete all items that are checked from both lists
        checked_items = shoppinglist.checked
        print(f"Checked items: {checked_items}")
        for item in checked_items:
            name = item.text
            if self.db.item_exists("shopping",name):
                self.db.del_item("shopping",name)
            item.delete()
        self.keep.sync()


    def string(self, lists):
        """ Convert a python list into a string such as 'a, b and c' """
        conj_spaced = ' {} '.format("and")
        return ', '.join(lists[:-2] + [conj_spaced.join(lists[-2:])])


def create_skill():
    return SimpleShoppingList()
