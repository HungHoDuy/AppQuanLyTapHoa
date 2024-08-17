from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.screenmanager import ScreenManager, Screen
from pymongo import MongoClient
import datetime
import cv2
from pyzbar import pyzbar
import pygame

def scan_barcode():
    # Initialize pygame mixer for playing sound
    pygame.mixer.init()

    # Load the scanner sound
    scanner_sound = pygame.mixer.Sound("scanner_sound.mp3")

    # Start video capture
    cap = cv2.VideoCapture(0)

    try:
        while True:
            # Capture frame-by-frame
            ret, frame = cap.read()

            if not ret:
                print("Failed to capture image")
                break

            # Decode the barcode(s) in the frame
            barcodes = pyzbar.decode(frame)

            for barcode in barcodes:
                # Convert the barcode data to a string
                barcode_data = barcode.data.decode("utf-8")
                print(f"Scanned barcode: {barcode_data}")

                # Play the scanner sound
                scanner_sound.play()

                # Release the capture and close the windows
                cap.release()
                cv2.destroyAllWindows()

                return barcode_data

            # Display the frame with the barcode detection
            cv2.imshow("Barcode Scanner", frame)

            # Check if 'q' is pressed to quit
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    finally:
        # Release the capture and close the windows
        cap.release()
        cv2.destroyAllWindows()

    return None

class MainScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical')

        self.add_item_button = Button(text="Thêm sản phẩm")
        self.add_item_button.bind(on_press=self.go_to_add_item)
        layout.add_widget(self.add_item_button)

        self.search_item_button = Button(text="Kiếm sản phẩm")
        self.search_item_button.bind(on_press=self.go_to_search_item)
        layout.add_widget(self.search_item_button)

        self.make_bill_button = Button(text="Tạo hóa đơn")
        self.make_bill_button.bind(on_press=self.go_to_make_bill)
        layout.add_widget(self.make_bill_button)

        self.add_widget(layout)

    def go_to_add_item(self, instance):
        self.manager.current = 'add_item'

    def go_to_search_item(self, instance):
        self.manager.current = 'search_item'

    def go_to_make_bill(self, instance):
        self.manager.current = 'make_bill'

class AddItemScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical')

        self.message_label = Label(text="Thêm Sản Phẩm")
        layout.add_widget(self.message_label)

        self.name_input = TextInput(hint_text="Nhập Tên")
        layout.add_widget(self.name_input)

        self.price_input = TextInput(hint_text="Nhập Giá", input_filter='int')
        layout.add_widget(self.price_input)

        self.scan_button = Button(text="Quét mã")
        self.scan_button.bind(on_press=self.scan_barcode)
        layout.add_widget(self.scan_button)

        self.barcode_label = Label(text="Mã của sản phẩm")
        layout.add_widget(self.barcode_label)

        self.add_button = Button(text="Thêm")
        self.add_button.bind(on_press=self.add_item)
        layout.add_widget(self.add_button)

        self.back_button = Button(text="Quay về trang chủ")
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
            self.barcode_label.text = f"Đã quét mã: {barcode}"
        else:
            self.barcode_label.text = "Quét mã thất bại."

    def add_item(self, instance):
        name = self.name_input.text.strip().lower()
        price = self.price_input.text.strip()

        if not name or not price or not self.scanned_barcode:
            self.message_label.text = "Tất cả các trường là bắt buộc!"
            return

        try:
            price = float(price)
        except ValueError:
            self.message_label.text = "Giá phải là một số."
            return

        collection = self.connect_to_mongo()

        existing_product = collection.find_one({"barcode": self.scanned_barcode})
        if existing_product:
            self.message_label.text = (
                f"Sản phẩm với mã này đã tồn tại:\n"
                f"Tên: {existing_product['name']}\n"
                f"Giá: {existing_product['price']} VND\n"
                f"Bạn có muốn sửa sản phẩm hiện tại không?"
            )
            self.add_button.text = "Sửa sản phẩm hiện tại"
            self.add_button.unbind(on_press=self.add_item)
            self.add_button.bind(on_press=self.modify_existing_item)
            return

        product = {
            "name": name,
            "price": price,
            "barcode": self.scanned_barcode
        }
        collection.insert_one(product)
        self.message_label.text = f"Đã thêm sản phẩm: {name}, Giá: {price} VND, Mã: {self.scanned_barcode}"

    def modify_existing_item(self, instance):
        name = self.name_input.text.strip().lower()
        price = self.price_input.text.strip()

        if not name or not price or not self.scanned_barcode:
            self.message_label.text = "Tất cả các trường là bắt buộc!"
            return

        try:
            price = int(float(price))
        except ValueError:
            self.message_label.text = "Giá phải là một số."
            return

        collection = self.connect_to_mongo()

        collection.update_one(
            {"barcode": self.scanned_barcode},
            {"$set": {"name": name, "price": price}}
        )
        self.message_label.text = f"Đã sửa sản phẩm: {name}, Giá: {price} VND, Mã: {self.scanned_barcode}"

        self.add_button.text = "Thêm"
        self.add_button.unbind(on_press=self.modify_existing_item)
        self.add_button.bind(on_press=self.add_item)

    def go_back(self, instance):
        self.manager.current = 'main'

class SearchItemScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical')

        self.message_label = Label(text="Kiếm sản phẩm")
        layout.add_widget(self.message_label)

        self.search_name_button = Button(text="Kiếm theo tên")
        self.search_name_button.bind(on_press=self.go_to_search_name)
        layout.add_widget(self.search_name_button)

        self.search_barcode_button = Button(text="Kiếm theo mã")
        self.search_barcode_button.bind(on_press=self.go_to_search_barcode)
        layout.add_widget(self.search_barcode_button)

        self.back_button = Button(text="Quay về trang chủ")
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

        self.message_label = Label(text="Kiếm theo tên")
        layout.add_widget(self.message_label)

        self.name_input = TextInput(hint_text="Nhập tên sản phẩm")
        layout.add_widget(self.name_input)

        self.search_button = Button(text="Kiếm")
        self.search_button.bind(on_press=self.search_by_name)
        layout.add_widget(self.search_button)

        self.modify_button = Button(text="Sửa", disabled=True)
        self.modify_button.bind(on_press=self.modify_product)
        layout.add_widget(self.modify_button)

        self.back_button = Button(text="Quay về")
        self.back_button.bind(on_press=self.go_back)
        layout.add_widget(self.back_button)

        self.add_widget(layout)

        self.found_product = None

    def connect_to_mongo(self):
        client = MongoClient('mongodb+srv://hungduyhoqaz:Hung2004@hung.gfnrjyb.mongodb.net/?retryWrites=true&w=majority&appName=Hung')
        db = client["QuanLyTapHoa"]
        collection = db["Products"]
        return collection

    def search_by_name(self, instance):
        name = self.name_input.text.strip().lower()
        if not name:
            self.message_label.text = "Vui lòng nhập tên sản phẩm."
            return

        collection = self.connect_to_mongo()
        self.found_product = collection.find_one({"name": name})

        if self.found_product:
            self.message_label.text = (
                f"Sản phẩm tìm thấy:\n"
                f"Tên: {self.found_product.get('name', 'N/A')}\n"
                f"Giá: {int(self.found_product.get('price', 'N/A'))} VND"
            )
            self.modify_button.disabled = False
        else:
            self.message_label.text = "Không tìm thấy sản phẩm"
            self.modify_button.disabled = True

    def modify_product(self, instance):
        if not self.found_product:
            return

        self.name_input.text = self.found_product.get('name', '')
        self.price_input = TextInput(hint_text="Nhập Giá", input_filter='int')
        self.price_input.text = str(self.found_product.get('price', ''))

        layout = self.children[0]
        layout.clear_widgets()

        layout.add_widget(Label(text="Sửa sản phẩm"))

        layout.add_widget(self.name_input)
        layout.add_widget(self.price_input)

        save_button = Button(text="Lưu thay đổi")
        save_button.bind(on_press=self.save_modifications)
        layout.add_widget(save_button)

        cancel_button = Button(text="Hủy")
        cancel_button.bind(on_press=self.go_back)
        layout.add_widget(cancel_button)

    def save_modifications(self, instance):
        new_name = self.name_input.text.strip()
        new_price = self.price_input.text.strip()

        if not new_name or not new_price:
            self.message_label.text = "Tất cả các trường là bắt buộc!"
            return

        try:
            new_price = int(float(new_price))
        except ValueError:
            self.message_label.text = "Giá phải là một số."
            return

        collection = self.connect_to_mongo()

        # Update the product with the new values
        collection.update_one(
            {"_id": self.found_product["_id"]},
            {"$set": {"name": new_name, "price": int(new_price)}}
        )

        self.message_label.text = f"Đã lưu thay đổi cho sản phẩm: {new_name}, Giá mới: {new_price} VND"
        self.modify_button.disabled = True

        # Return to search screen
        self.go_back(None)

    def go_back(self, instance):
        self.manager.current = 'search_item'

class SearchBarcodeScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical')

        self.message_label = Label(text="Kiếm theo mã")
        layout.add_widget(self.message_label)

        self.scan_button = Button(text="Quét mã")
        self.scan_button.bind(on_press=self.scan_barcode)
        layout.add_widget(self.scan_button)

        self.modify_button = Button(text="Sửa", disabled=True)
        self.modify_button.bind(on_press=self.modify_product)
        layout.add_widget(self.modify_button)

        self.back_button = Button(text="Quay về")
        self.back_button.bind(on_press=self.go_back)
        layout.add_widget(self.back_button)

        self.add_widget(layout)

        self.found_product = None
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
            collection = self.connect_to_mongo()
            self.found_product = collection.find_one({"barcode": barcode})

            if self.found_product:
                self.message_label.text = (
                    f"Sản phẩm tìm thấy:\n"
                    f"Tên: {self.found_product.get('name', 'N/A')}\n"
                    f"Giá: {int(self.found_product.get('price', 'N/A'))} VND"
                )
                self.modify_button.disabled = False
            else:
                self.message_label.text = "Không tìm thấy sản phẩm với mã này."
                self.modify_button.disabled = True
        else:
            self.message_label.text = "Quét mã thất bại."

    def modify_product(self, instance):
        if not self.found_product:
            return

        self.name_input = TextInput(hint_text="Nhập Tên")
        self.name_input.text = self.found_product.get('name', '')
        self.price_input = TextInput(hint_text="Nhập Giá", input_filter='int')
        self.price_input.text = str(self.found_product.get('price', ''))

        layout = self.children[0]
        layout.clear_widgets()

        layout.add_widget(Label(text="Sửa sản phẩm"))

        layout.add_widget(self.name_input)
        layout.add_widget(self.price_input)

        save_button = Button(text="Lưu thay đổi")
        save_button.bind(on_press=self.save_modifications)
        layout.add_widget(save_button)

        cancel_button = Button(text="Hủy")
        cancel_button.bind(on_press=self.go_back)
        layout.add_widget(cancel_button)

    def save_modifications(self, instance):
        new_name = self.name_input.text.strip()
        new_price = self.price_input.text.strip()

        if not new_name or not new_price:
            self.message_label.text = "Tất cả các trường là bắt buộc!"
            return

        try:
            new_price = int(float(new_price))
        except ValueError:
            self.message_label.text = "Giá phải là một số."
            return

        collection = self.connect_to_mongo()

        collection.update_one(
            {"_id": self.found_product["_id"]},
            {"$set": {"name": new_name, "price": new_price}}
        )

        self.message_label.text = f"Đã lưu thay đổi cho sản phẩm: {new_name}, Giá mới: {new_price} VND"
        self.modify_button.disabled = True

        # Return to search screen
        self.go_back(None)

    def go_back(self, instance):
        self.manager.current = 'search_item'

class MakeBillScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical')

        self.message_label = Label(text="Tạo hóa đơn")
        layout.add_widget(self.message_label)

        self.product_input = TextInput(hint_text="Nhập tên sản phẩm hoặc quét mã")
        layout.add_widget(self.product_input)

        self.scan_barcode_button = Button(text="Quét mã vạch")
        self.scan_barcode_button.bind(on_press=self.scan_barcode_action)
        layout.add_widget(self.scan_barcode_button)

        self.quantity_input = TextInput(hint_text="Số lượng", text="1", input_filter='int', multiline=False)
        layout.add_widget(self.quantity_input)

        self.add_product_button = Button(text="Thêm sản phẩm vào hóa đơn")
        self.add_product_button.bind(on_press=self.add_product_to_bill)
        layout.add_widget(self.add_product_button)

        self.bill_label = Label(text="Hóa đơn:")
        layout.add_widget(self.bill_label)

        self.total_label = Label(text="Tổng cộng: 0 VND")
        layout.add_widget(self.total_label)

        self.complete_button = Button(text="Hoàn tất hóa đơn")
        self.complete_button.bind(on_press=self.complete_bill)
        layout.add_widget(self.complete_button)

        self.back_button = Button(text="Quay về trang chủ")
        self.back_button.bind(on_press=self.go_back)
        layout.add_widget(self.back_button)

        self.add_widget(layout)

        self.bill_items = []
        self.total_price = 0

    def scan_barcode_action(self, instance):
        barcode = scan_barcode()
        if barcode:
            self.product_input.text = barcode
            self.quantity_input.text = "1"  # Set default quantity to 1
        else:
            self.message_label.text = "Quét mã thất bại."

    def add_product_to_bill(self, instance):
        product_name_or_barcode = self.product_input.text.strip().lower()
        quantity_str = self.quantity_input.text.strip()

        if not product_name_or_barcode:
            self.message_label.text = "Vui lòng nhập tên sản phẩm hoặc quét mã."
            return

        if not quantity_str:
            self.message_label.text = "Vui lòng nhập số lượng."
            return

        try:
            quantity = int(quantity_str)
        except ValueError:
            self.message_label.text = "Số lượng phải là số nguyên hợp lệ."
            return

        if quantity <= 0:
            self.message_label.text = "Vui lòng nhập số lượng hợp lệ."
            return

        collection = self.connect_to_mongo()["Products"]
        product = collection.find_one({
            "$or": [{"name": product_name_or_barcode}, {"barcode": product_name_or_barcode}]
        })

        if product:
            price = int(product['price'])  # Ensure price is an integer
            total_item_price = price * quantity
            self.bill_items.append({
                'name': product['name'],
                'quantity': quantity,
                'total_price': total_item_price
            })
            self.total_price += total_item_price
            self.bill_label.text += f"\n{product['name']} (x{quantity}) - {total_item_price} VND"
            self.total_label.text = f"Tổng cộng: {self.total_price} VND"
            self.message_label.text = "Đã thêm sản phẩm vào hóa đơn."
        else:
            self.message_label.text = "Không tìm thấy sản phẩm."

    def complete_bill(self, instance):
        self.save_bill_to_db()  # Save the bill to the database
        self.message_label.text = "Hóa đơn đã hoàn tất."
        # Reset the bill
        self.bill_items = []
        self.total_price = 0
        self.bill_label.text = "Hóa đơn:"
        self.total_label.text = "Tổng cộng: 0 VND"
        self.product_input.text = ""
        self.quantity_input.text = "1"  # Reset default quantity to 1

    def connect_to_mongo(self):
        client = MongoClient('mongodb+srv://hungduyhoqaz:Hung2004@hung.gfnrjyb.mongodb.net/?retryWrites=true&w=majority&appName=Hung')
        db = client["QuanLyTapHoa"]
        return db

    def save_bill_to_db(self):
        collection = self.connect_to_mongo()["Bills"]
        bill_data = {
            'items': self.bill_items,
            'total_price': self.total_price,
            'timestamp': datetime.datetime.now()
        }
        collection.insert_one(bill_data)

    def go_back(self, instance):
        self.manager.current = 'main'

class QuanLyTapHoaApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(MainScreen(name='main'))
        sm.add_widget(AddItemScreen(name='add_item'))
        sm.add_widget(SearchItemScreen(name='search_item'))
        sm.add_widget(SearchNameScreen(name='search_name'))
        sm.add_widget(SearchBarcodeScreen(name='search_barcode'))
        sm.add_widget(MakeBillScreen(name='make_bill'))
        return sm


if __name__ == '__main__':
    QuanLyTapHoaApp().run()