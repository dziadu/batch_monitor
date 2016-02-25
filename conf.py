from django.conf import settings
from os.path import dirname, basename, isfile
import glob

USER_MAP = {}

class BatchMonitorConf(object):
	def __init__(self):
		self.f_user_map = None

		modules = glob.glob(dirname("batch_monitor/confs/")+"/*.py")
		__all__ = [ basename(f)[:-3] for f in modules if isfile(f)]
		for module in __all__:
			if module == '__init__':
				continue
			mod = __import__("batch_monitor.confs."+module, locals(), globals(), ['USER_MAP'], -1)
			if hasattr(mod, 'USER_MAP'):
				self.f_user_map = mod.USER_MAP
			else:
				print("No user map");

	@property
	def user_map(self):
		return self.f_user_map


config = BatchMonitorConf()
