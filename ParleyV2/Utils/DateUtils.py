from datetime import date


class DateUtils:

    def get_todays_date_string():
        today = date.today()
        return today.strftime("%d/%m/%Y")