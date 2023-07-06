class UserData:
    def __init__(self):
        self.customer_name = ""
        self.customer_email = ""
        self.selected_car = ""

    def get_user_info(self, customer_name="", customer_email="", selected_car=""):
        if customer_name:
            self.customer_name = customer_name
        if customer_email:
            self.customer_email = customer_email
        if selected_car:
            self.selected_car = selected_car

        self.print_user_info()

    def get_data(self):
        return {
            "customer_name": self.customer_name,
            "customer_email": self.customer_email,
            "selected_car": self.selected_car
        }
    
    def print_user_info(self):
        print("Name:", self.customer_name)
        print("Email:", self.customer_email)
        print("Car:", self.selected_car)
