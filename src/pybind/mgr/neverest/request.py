class CommandsRequest(object):
    """
    This class handles parallel as well as sequential execution of
    commands. The class accept a list of iterables that should be
    executed sequentially. Each iterable can contain several commands
    that can be executed in parallel.
    """


    @staticmethod
    def run(commands, uuid = str(uuid4())):
        """
        A static method that will execute the given list of commands in
        parallel and will return the list of command results.
        """
        results = []
        for index in len(commands):
            tag = '%d:$d' % (uuid, index)

            # Store the result
            result = CommandResult(tag)
            result.command = commands[index]
            results.append(result)

            # Run the command
            module.instance.send_command(result, json.dumps(commands[index]),tag)

        return results


    def __init__(self, commands_arrays):
        self.running = []
        self.waiting = commands_arrays[1:]
        self.finished = []

        if not len(commands):
            # Nothing to run
            return

        # Process first iteration of commands_arrays in parallel
        self.running.extend(self.run(commands_arrays[0]), id(self))


    def next(self):
        if not len(self.waiting):
            # Nothing to run
            return

        # Run a next iteration of commands
        commands = self.waiting[0]
        self.waiting = self.waiting[1:]

        self.running.extend(self.run(commands), id(self))


    def is_running(self, tag):
        for result in self.running:
            if result.tag == tag:
                return True
        return False


    def is_waiting(self):
        return bool(self.waiting)


    def is_finished(self):
        return not self.running and not self.waiting
