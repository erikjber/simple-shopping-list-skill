from mycroft import MycroftSkill, intent_file_handler
from .database import Database
from escpos.connections import getNetworkPrinter
from .category_sorter import sort_items

LIST_NAME = "shopping"

class SimpleShoppingList(MycroftSkill):
    def __init__(self):
        MycroftSkill.__init__(self)
        self.db = Database()

    def _ensure_list_exists(self):
        """If the list does not exits, create it."""
        if not self.db.list_exists(LIST_NAME):
            self.db.add_list(LIST_NAME)

    @intent_file_handler('add.intent')
    def handle_add(self, message):
        self._ensure_list_exists()
        item = message.data.get("item")
        data = {"item":item}
        if item:
            if self.db.item_exists("shopping",item):
                self.speak_dialog('already_exists',data)
            else:
                self.db.add_item("shopping",item)
                self.speak_dialog('add',data)

    @intent_file_handler('read.intent')
    def handle_read(self, message):
        data = {}
        self._ensure_list_exists()
        if self.db.list_empty("shopping"):
            self.speak_dialog('list_is_empty')
        else:
            data['items'] = self.string(self.db.read_items("shopping"))
            self.speak_dialog('read_items', data)

    @intent_file_handler('count.intent')
    def handle_count(self, message):
        data = {}
        self._ensure_list_exists()
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


    @intent_file_handler('delete.intent')
    def handle_delete(self, message):
        item = message.data.get("item")
        self._ensure_list_exists()
        if self.db.list_empty("shopping"):
            self.speak_dialog('list_is_empty')
        else:
            self.delete_item(item)


    def delete_item(self, item: str):
        if self.confirm_deletion(item):
            self.db.del_item("shopping", item)
            self.speak_dialog('deleted', {"item":item})


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
            self.speak_dialog('list_is_empty')
        else:
            self.speak_dialog('cancelled')
        return False


    def string(self, lists):
        """ Convert a python list into a string such as 'a, b and c' """
        conj_spaced = ' {} '.format("and")
        return ', '.join(lists[:-2] + [conj_spaced.join(lists[-2:])])


def create_skill():
    return SimpleShoppingList()
