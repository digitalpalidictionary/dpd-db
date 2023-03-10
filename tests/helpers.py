class InternalTestRow():
    def __init__(
        self, test_name,
        search_column_1, search_sign_1, search_string_1,
        search_column_2, search_sign_2, search_string_2,
        search_column_3, search_sign_3, search_string_3,
        search_column_4, search_sign_4, search_string_4,
        search_column_5, search_sign_5, search_string_5,
        search_column_6, search_sign_6, search_string_6,
        error_column, error_message,
            exceptions, iterations):

        self.test_name = test_name
        self.search_column_1 = search_column_1
        self.search_sign_1 = search_sign_1
        self.search_string_1 = search_string_1
        self.search_column_2 = search_column_2
        self.search_sign_2 = search_sign_2
        self.search_string_2 = search_string_2
        self.search_column_3 = search_column_3
        self.search_sign_3 = search_sign_3
        self.search_string_3 = search_string_3
        self.search_column_4 = search_column_4
        self.search_sign_4 = search_sign_4
        self.search_string_4 = search_string_4
        self.search_column_5 = search_column_5
        self.search_sign_5 = search_sign_5
        self.search_string_5 = search_string_5
        self.search_column_6 = search_column_6
        self.search_sign_6 = search_sign_6
        self.search_string_6 = search_string_6
        self.error_column = error_column
        self.error_message = error_message
        self.exceptions = set(exceptions.split(", "))
        self.iterations = iterations

    def __repr__(self) -> str:
        return f"InternalTestRow: {self.test_name} {self.show_error_message}"
