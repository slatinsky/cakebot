class TablePrint:
    def __init__(self, widths: tuple):
        self.widths = widths

    def print_row(self, row):
        counter = 0
        ret_str = ""
        for column in row:
            width_correction = 0
            uncolored_string = str(column)

            width_correction = max(0, len(str(column)) - len(uncolored_string))
            ret_str += str(column).ljust(self.widths[counter] + width_correction)
            counter += 1
        ret_str += "\n"
        return ret_str
