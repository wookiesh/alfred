import logging
import os
from alfred import eventBus
from alfred.bindings import Binding
from alfred import config

items = {}
activeBindings = {}
db = None

bus = None
log = logging.getLogger(__name__)

def stop():
    for b in activeBindings:
        activeBindings[b].stop()

def getAvailableBindings():
    """
    Check for all bindings available
    TODO: make this more robust
    """

    import alfred
    res, bindingPath = [], os.path.join(os.path.dirname(alfred.__file__), 'bindings')
    for d in os.listdir(bindingPath):
        if os.path.isdir(os.path.join(bindingPath, d)) and not d.endswith('egg-info'):
            res.append(d)
    return res

def startInstalled():
    log.info("Available bindings: %s" % getAvailableBindings())
    bus = eventBus.create()
    for i in filter(lambda i: i[1]['autoStart'], config.get('bindings').items()):
        startBinding(i[0])

    # Then fetch item definition
    log.info('Available items: %s' % [x.get('name') for x in config.get('items')])
    for itemDef in config.get('items'):
        register(**itemDef)

def installBinding(bindingName):
    __import__('alfred.bindings.%s' % bindingName)

    if not (db.bindings.find_one({'name': bindingName})):
        db.bindings.insert(dict(
            name=bindingName,
            autoStart=False,
            config={}
        ))

def uninstallBinding(bindingName):
    if bindingName in activeBindings:
        stopBinding(bindingName)
    db.bindings.remove({'name': bindingName})

def startBinding(bindingName):
    log.info("Starting binding %s" % bindingName)
    __import__('alfred.bindings.%s' % bindingName)
    instance = Binding.plugins[bindingName]()
    activeBindings[bindingName] = instance
    instance.start()

def stopBinding(bindingName):
    log.info('Stopping binding %s' % bindingName)
    b = activeBindings[bindingName]
    b.stop()
    del b

def register(name, type, binding, groups=None, **kwargs):
    if name in items:
        if items[name].type == type:
            return items[name]
        else:
            raise Exception("Item with name %s already defined with type %s" %
                           (name, items[name].type))
    else:
        bind = binding.split(':')[0]
        if bind not in activeBindings:
            raise Exception('Binding %s not installed or started' % bind)
        else:
            item = activeBindings[bind].register(name, type, binding.split(':')[1:], groups)
            item.bus = bus

        items[name] = item
        return item

    return items.get(name, None)