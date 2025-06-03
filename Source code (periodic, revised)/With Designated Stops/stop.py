class Stop:
    def __init__(self, position, stop_id):
        self.position = position
        self.stop_id = stop_id
        self.loading_list = []
        self.unloading_list = []
        self.unloading_dictionary = {}

    