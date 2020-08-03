from batch_farm_monitor.farms.farm_abstract import Command, UserData, FairShareEngine

class Diagnose(FairShareEngine):
	def __init__(self, remote):
		super(Diagnose, self).__init__(remote)
		self.cmd = "diagnose -f"

	def parse(self, users_list):
		text = data

		_waitline=0
		_parse_user = False
		_parse_group = False

		for line in text.splitlines():
			if line == "USER":
				_parse_user = True
				_waitline = 1
				continue
			if line == "GROUP":
	#			_parse_group = True
				_waitline = 1
				continue
			if line == "":
				_parse_user = _parse_group = False
				continue

			if _parse_user:
				if _waitline > 0:
					_waitline -= 1
				else:
					words = line.split()
					if words[0][-1] == "*":
						_uname = words[0][:-1]
					else:
						_uname = words[0]
					_uname = _uname[0:8]

					if _uname not in users_list:
						print("Adding user " + _uname)
						users_list[_uname] = UserData(_uname)

					_fair = float(words[1])
					users_list[_uname].clear()
					users_list[_uname].fairshare = 100.0 - _fair

