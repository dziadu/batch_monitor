def js_call_extractor(str0):
	
	str1 = str0.replace("\"$@#", "")
	str2 = str1.replace("#@$\"", "")
	return str2
