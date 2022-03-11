from mycroft import MycroftSkill, intent_file_handler


class SimpleShoppingList(MycroftSkill):
    def __init__(self):
        MycroftSkill.__init__(self)

    @intent_file_handler('list.shopping.simple.intent')
    def handle_list_shopping_simple(self, message):
        self.speak_dialog('list.shopping.simple')


def create_skill():
    return SimpleShoppingList()

