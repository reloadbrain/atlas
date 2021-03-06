from . import Interpreter
from snips_nlu import load_resources, SnipsNLUEngine, __version__
from snips_nlu.builtin_entities import BuiltinEntityParser, is_builtin_entity
import io, json, os

def get_entity_value(entity, default_value=None):
  """Retrieve an entity value.
  
  :param entity: Dictionary wich contains results
  :type entity: dict
  :param default_value: Default value if not found
  :type default_value: any

  """

  return entity.get('value', entity.get('from', default_value))

class SnipsInterpreter(Interpreter):

  def __init__(self):
    super(SnipsInterpreter, self).__init__('snips')

    self._meta = None
    self._lang = None
    self._engine = None
    self._entity_parser = None

    self._log.info('Using snips-nlu version %s' % __version__)

  def metadata(self):
    return self._meta

  def lang(self):
    return self._lang

  def fit(self, training_file_path, trained_directory_path):
    filename, _ = os.path.splitext(os.path.basename(training_file_path))

    # TODO check what should be in the base Interpreter class

    trained_path = os.path.join(trained_directory_path, '%s.trained.json' % filename)
    checksum_path = os.path.join(trained_directory_path, '%s.checksum' % filename)

    with open(training_file_path) as f:
      training_str = f.read()
      training_data = json.loads(training_str)
      self._lang = training_data['language']
      self._log.info('Loading resources for language %s' % self._lang)
      load_resources(self._lang)

    same, computed_checksum = self.checksum_match(training_str, checksum_path)

    # Checksums match, load the engine from trained file
    if same and os.path.isfile(trained_path):
      self._log.info('Checksum matched, loading trained engine')
      with open(trained_path) as f:
        self._engine = SnipsNLUEngine.from_dict(json.load(f))  
    else:
      self._log.info('Checksum has changed, retraining the engine')
      self._engine = SnipsNLUEngine()
      self._engine.fit(training_data)

      with open(trained_path, mode='w') as f:
        json.dump(self._engine.to_dict(), f)

      with open(checksum_path, mode='w') as f:
        f.write(computed_checksum)

    self._entity_parser = BuiltinEntityParser(self._lang)
    self._meta = { k: list(v.keys()) for k, v in self._engine._dataset_metadata['slot_name_mappings'].items() }

  def parse_entity(self, msg, intent, slot):
    entity_label = self._engine._dataset_metadata['slot_name_mappings'].get(intent, {}).get(slot)

    # TODO try to find a way to retrieve multiple slot values, that's a hard one
    # May be we can try matching on _dataset_metadata['entities']

    if is_builtin_entity(entity_label):
      parsed = self._entity_parser.parse(msg)

      if parsed:
        return get_entity_value(parsed[0]['entity'], msg)

    return msg

  def parse(self, msg):

    # TODO manage multiple intents in the same sentence

    parsed = self._engine.parse(msg)

    if parsed['intent'] == None:
      return []

    slots = {}

    # Constructs a slot dictionary with slot value as a list if multiples matched
    for slot in parsed['slots']:
      name = slot['slotName']
      value = get_entity_value(slot['value'])

      if name in slots:
        if type(slots[name]) is not list:
          slots[name] = [slots[name]]

        slots[name].append(value)
      else:
        slots[name] = value

    return [{
      'text': msg,
      'intent': parsed['intent']['intentName'],
      'slots': slots,
    }]