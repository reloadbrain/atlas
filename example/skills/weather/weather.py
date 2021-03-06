from atlas_sdk import SkillClient, Intent, Slot, Env, Request
import time
from dateutil.parser import parse as dateParse

def get_forecasts(request):
  """
  :type request: Request

  """

  date = request.slot('weatherDate', converter=dateParse)

  if not date:
    return request.ask('weatherDate', _('For when do you want the forecast?')) # pylint: disable=E0602

  location = request.slot('weatherLocation')

  if not location:
    return request.ask('weatherLocation', _('For where do you want the forecast?')) # pylint: disable=E0602

  time.sleep(3)

  api_key = request.env('WEATHER_API_KEY') # pylint: disable=W0612

  request.show(_("Well, I'll try to find the forecasts for %s on %s") % (location, date), terminate=True)  # pylint: disable=E0602

if __name__ == '__main__':
  weather_skill = SkillClient(
    name='weather',
    version='1.0.0',
    author='Julien LEICHER',
    description='Gives some weather forecasts',
    intents=[
      Intent('sampleGetWeather', get_forecasts, [Slot('weatherDate'), Slot('weatherLocation')])
    ],
    env=[Env('WEATHER_API_KEY')]
  )

  weather_skill.run()
