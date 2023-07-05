class UserData:
    def __init__(self):
        self.name = ""
        self.email = ""
        self.car = ""

    def get_user_info(self, name="", email="", car=""):
        if name:
            self.name = name
        if email:
            self.email = email
        if car:
            self.car = car

        self.print_user_info()

    def get_data(self):
        return {
            "name": self.name,
            "email": self.email,
            "car": self.car
        }
    
    def print_user_info(self):
        print("Name:", self.name)
        print("Email:", self.email)
        print("Car:", self.car)
