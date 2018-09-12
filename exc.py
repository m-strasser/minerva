class InvalidISBNError(Exception):
    def __init__(self, ex):
        super(InvalidISBNError, self).__init__(ex)


class NoResultsError(Exception):
    def __init__(self, ex):
        super(NoResultsError, self).__init__(ex)
