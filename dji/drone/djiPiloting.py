class DJIPiloting:
    def __init__(self, drone_object):
        self.drone = drone_object
        self.action_queue = []

    def takeoff(self, queue=False):
        if not queue:
            print("------ TAKEOFF ------")
        else:
            self.add_action(self.takeoff)

    def land(self, queue=False):
        if not queue:
            print("------ LAND ------")
        else:
            self.add_action(self.land)

    def wait_until_state(self, state_type, state, timeout=None):
        pass

    def move_by(self, x, y, z, angle, wait=False, queue=False):
        pass

    def move_to(self, lat, lon, alt, orientation_mode="NONE", heading=0, wait=False, queue=False):
        pass

    def cancel_move_by(self):
        pass

    def cancel_move_to(self):
        pass

    def add_action(self, action):
        pass

    def remove_action(self, index):
        pass

    def clear_actions(self):
        self.action_queue = []

    def execute_actions(self, num=-1):
        if num < 0:
            num = len(self.action_queue)

        for _ in range(num):
            action = self.action_queue.pop(0)
            action()
