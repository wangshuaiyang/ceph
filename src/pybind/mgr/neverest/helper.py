# List of valid osd flags
OSD_FLAGS = ('pause', 'noup', 'nodown', 'noout', 'noin', 'nobackfill', 'norecover', 'noscrub', 'nodeep-scrub')

# Helper function to catch and log the exceptions
def catch(f):
    def catcher(*args, **kwargs):
        import module
        try:
            return f(*args, **kwargs)
        except:
            module.instance.log.error(str(traceback.format_exc()))
    return catcher
