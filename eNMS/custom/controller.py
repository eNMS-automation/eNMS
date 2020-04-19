from flask import Blueprint, render_template, request


class CustomController:
    def process_form_data(self, **data):
        print(data)
        return data
