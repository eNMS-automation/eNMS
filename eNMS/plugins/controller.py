class CustomController:
    def process_form_data(self, **data):
        return data["router_id"] * 2
