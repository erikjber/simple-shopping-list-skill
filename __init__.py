from mycroft import MycroftSkill, intent_file_handler
from .database import Database


class SimpleShoppingList(MycroftSkill):
    def __init__(self):
        MycroftSkill.__init__(self)
        self.db = Database()

    @intent_file_handler('add.intent')
    def handle_add(self, message):
        if not self.db.list_exists("shopping"):
            self.db.add_list("shopping")
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
        if not self.db.list_exists("shopping"):
            self.db.add_list("shopping")
        if self.db.list_empty("shopping"):
            self.speak_dialog('list_is_empty')
        else:
            data['items'] = self.string(self.db.read_items("shopping"))
            self.speak_dialog('read_items', data)

    @intent_file_handler('delete_last.intent')
    def handle_delete_last(self, message):
        if not self.db.list_exists("shopping"):
            self.db.add_list("shopping")
        if self.db.list_empty("shopping"):
            self.speak_dialog('list_is_empty')
        else:
            item = self.db.read_items("shopping")[-1]
            self.delete_item(item)


    @intent_file_handler('delete.intent')
    def handle_delete(self, message):
        item = message.data.get("item")
        if not self.db.list_exists("shopping"):
            self.db.add_list("shopping")
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


    def string(self, lists):
        """ Convert a python list into a string such as 'a, b and c' """
        conj_spaced = ' {} '.format("and")
        return ', '.join(lists[:-2] + [conj_spaced.join(lists[-2:])])


def create_skill():
    return SimpleShoppingList()
