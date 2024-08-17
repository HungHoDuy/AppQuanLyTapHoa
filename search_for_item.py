from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.screenmanager import ScreenManager, Screen
from add_item import scan_barcode
from pymongo import MongoClient

class MainScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical')

        self.add_item_button = Button(text="Add Item")
        self.add_item_button.bind(on_press=self.go_to_add_item)
        layout.add_widget(self.add_item_button)

        self.search_item_button = Button(text="Search for Item")
        self.search_item_button.bind(on_press=self.go_to_search_item)
        layout.add_widget(self.search_item_button)

        self.add_widget(layout)

    def go_to_add_item(self, instance):
        self.manager.current = 'add_item'

    def go_to_search_item(self, instance):
        self.manager.current = 'search_item'

class AddItemScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical')

        self.message_label = Label(text="Add Item")
        layout.add_widget(self.message_label)

        self.name_input = TextInput(hint_text="Enter product name")
        layout.add_widget(self.name_input)

        self.price_input = TextInput(hint_text="Enter product price", input_filter='float')
        layout.add_widget(self.price_input)

        # Replace barcode input with a scan button
        self.scan_button = Button(text="Scan Barcode")
        self.scan_button.bind(on_press=self.scan_barcode)
        layout.add_widget(self.scan_button)

        self.barcode_label = Label(text="Barcode will appear here")
        layout.add_widget(self.barcode_label)

        self.add_button = Button(text="Add Item")
        self.add_button.bind(on_press=self.add_item)
        layout.add_widget(self.add_button)

        self.back_button = Button(text="Back to Main Menu")
        self.back_button.bind(on_press=self.go_back)
        layout.add_widget(self.back_button)

        self.add_widget(layout)

        self.scanned_barcode = None

    def connect_to_mongo(self):
        client = MongoClient('mongodb+srv://hungduyhoqaz:Hung2004@hung.gfnrjyb.mongodb.net/?retryWrites=true&w=majority&appName=Hung')
        db = client["QuanLyTapHoa"]
        collection = db["Products"]
        return collection

    def scan_barcode(self, instance):
        barcode = scan_barcode()
        if barcode:
            self.scanned_barcode = barcode
            self.barcode_label.text = f"Scanned Barcode: {barcode}"
        else:
            self.barcode_label.text = "Barcode scan failed."

    def add_item(self, instance):
        name = self.name_input.text.strip()
        price = self.price_input.text.strip()

        if not name or not price or not self.scanned_barcode:
            self.message_label.text = "All fields are required!"
            return

        try:
            price = float(price)
        except ValueError:
            self.message_label.text = "Price must be a number."
            return

        collection = self.connect_to_mongo()
        product = {
            "name": name,
            "price": price,
            "barcode": self.scanned_barcode
        }
        collection.insert_one(product)
        self.message_label.text = f"Product added: {name}, Price: {price}, Barcode: {self.scanned_barcode}"

    def go_back(self, instance):
        self.manager.current = 'main'

class SearchItemScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical')

        self.message_label = Label(text="Search for Item")
        layout.add_widget(self.message_label)

        self.search_name_button = Button(text="Search by Name")
        self.search_name_button.bind(on_press=self.go_to_search_name)
        layout.add_widget(self.search_name_button)

        self.search_barcode_button = Button(text="Search by Scanning Barcode")
        self.search_barcode_button.bind(on_press=self.go_to_search_barcode)
        layout.add_widget(self.search_barcode_button)

        self.back_button = Button(text="Back to Main Menu")
        self.back_button.bind(on_press=self.go_back)
        layout.add_widget(self.back_button)

        self.add_widget(layout)

    def go_to_search_name(self, instance):
        self.manager.current = 'search_name'

    def go_to_search_barcode(self, instance):
        self.manager.current = 'search_barcode'

    def go_back(self, instance):
        self.manager.current = 'main'

class SearchNameScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical')

        self.message_label = Label(text="Search by Name")
        layout.add_widget(self.message_label)

        self.name_input = TextInput(hint_text="Enter product name")
        layout.add_widget(self.name_input)

        self.search_button = Button(text="Search")
        self.search_button.bind(on_press=self.search_by_name)
        layout.add_widget(self.search_button)

        self.back_button = Button(text="Back")
        self.back_button.bind(on_press=self.go_back)
        layout.add_widget(self.back_button)

        self.add_widget(layout)

    def connect_to_mongo(self):
        client = MongoClient('mongodb+srv://hungduyhoqaz:Hung2004@hung.gfnrjyb.mongodb.net/?retryWrites=true&w=majority&appName=Hung')
        db = client["QuanLyTapHoa"]
        collection = db["Products"]
        return collection

    def search_by_name(self, instance):
        name = self.name_input.text.strip()
        if not name:
            self.message_label.text = "Please enter a product name."
            return

        collection = self.connect_to_mongo()
        result = collection.find_one({"name": name})

        if result:
            self.message_label.text = f"Found product: {result}"
        else:
            self.message_label.text = "No product found with that name."

    def go_back(self, instance):
        self.manager.current = 'search_item'

class SearchBarcodeScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical')

        self.message_label = Label(text="Search by Scanning Barcode")
        layout.add_widget(self.message_label)

        self.search_button = Button(text="Scan Barcode")
        self.search_button.bind(on_press=self.scan_and_search)
        layout.add_widget(self.search_button)

        self.back_button = Button(text="Back")
        self.back_button.bind(on_press=self.go_back)
        layout.add_widget(self.back_button)

        self.add_widget(layout)

    def connect_to_mongo(self):
        client = MongoClient('mongodb+srv://hungduyhoqaz:Hung2004@hung.gfnrjyb.mongodb.net/?retryWrites=true&w=majority&appName=Hung')
        db = client["QuanLyTapHoa"]
        collection = db["Products"]
        return collection

    def scan_and_search(self, instance):
        barcode = scan_barcode()
        if not barcode:
            self.message_label.text = "No barcode scanned."
            return

        collection = self.connect_to_mongo()
        result = collection.find_one({"barcode": barcode})

        if result:
            self.message_label.text = f"Found product: {result}"
        else:
            self.message_label.text = "No product found with that barcode."

    def go_back(self, instance):
        self.manager.current = 'search_item'

class AddItemApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(MainScreen(name='main'))
        sm.add_widget(AddItemScreen(name='add_item'))
        sm.add_widget(SearchItemScreen(name='search_item'))
        sm.add_widget(SearchNameScreen(name='search_name'))
        sm.add_widget(SearchBarcodeScreen(name='search_barcode'))
        return sm

if __name__ == "__main__":
    AddItemApp().run()
