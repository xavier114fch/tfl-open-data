import time, os, requests, json, asyncio, math

data_dir = 'data'

def retryRequest(url):
	while True:
		r = requests.get(url)

		if r.status_code == 200:
			return r

		elif r.status_code == 429:
			time.sleep(1)

		else:
			raise Exception(r.status_code, url)

def scrub(obj, bad_key):
	if isinstance(obj, dict):
		# the call to `list` is useless for py2 but makes
		# the code py2/py3 compatible
		for key in list(obj.keys()):
			if key == bad_key:
				del obj[key]
			else:
				scrub(obj[key], bad_key)
	elif isinstance(obj, list):
		for i in reversed(range(len(obj))):
			if obj[i] == bad_key:
				del obj[i]
			else:
				scrub(obj[i], bad_key)

	else:
		# neither a dict nor a list, do nothing
		pass

def getModes():
	try:
		r = retryRequest('https://api.tfl.gov.uk/Line/Meta/Modes')

	except Exception as err:
		print('Cannot fetch valid modes.')
		getModes()

	else:
		_modes = r.json()
		modes = {}
		
		for _mode in _modes:
			if _mode['modeName'] not in modes:
				modes[_mode['modeName']] = {
					'isTflService': _mode['isTflService'],
					'isFarePaying': _mode['isFarePaying'],
					'isScheduledService': _mode['isScheduledService']
				}

		if not(os.path.isdir(data_dir)):
			os.mkdir(data_dir)

		with open(os.path.join(data_dir, 'tfl_modes.json'), 'w') as f:
			f.write(json.dumps(modes, ensure_ascii = False))
			print(f'Fetched {len(modes)} valid modes.')

def getServiceTypes():
	try:
		r = retryRequest('https://api.tfl.gov.uk/Line/Meta/ServiceTypes')

	except Exception as err:
		print('Cannot fetch valid service types.')
		getServiceTypes()

	else:
		types = r.json()

		if not(os.path.isdir(data_dir)):
			os.mkdir(data_dir)

		with open(os.path.join(data_dir, 'tfl_service_types.json'), 'w') as f:
			f.write(json.dumps(types, ensure_ascii = False))
			print(f'Fetched {len(types)} valid service types.')

def getDisruptionCategories():
	try:
		r = retryRequest('https://api.tfl.gov.uk/Line/Meta/DisruptionCategories')

	except Exception as err:
		print('Cannot fetch valid disruption categories.')
		getDisruptionCategories()

	else:
		categories = r.json()

		if not(os.path.isdir(data_dir)):
			os.mkdir(data_dir)

		with open(os.path.join(data_dir, 'tfl_disruption_categories.json'), 'w') as f:
			f.write(json.dumps(categories, ensure_ascii = False))
			print(f'Fetched {len(categories)} valid disruption categories.')

def getSeverity():
	try:
		r = retryRequest('https://api.tfl.gov.uk/Line/Meta/Severity')

	except Exception as err:
		print('Cannot fetch valid severities.')
		getSeverity()

	else:
		_severities = r.json()
		severities = {}
		
		for _severity in _severities:
			if _severity['modeName'] not in severities:
				severities[_severity['modeName']] = []
			severities[_severity['modeName']].append(_severity['description'])

		if not(os.path.isdir(data_dir)):
			os.mkdir(data_dir)

		with open(os.path.join(data_dir, 'tfl_severity.json'), 'w') as f:
			f.write(json.dumps(severities, ensure_ascii = False))
			print(f'Fetched {len(severities)} valid severities.')

def getStopTypes():
	try:
		r = retryRequest('https://api.tfl.gov.uk/StopPoint/Meta/stoptypes')

	except Exception as err:
		print('Cannot fetch valid stop types.')
		getStopTypes()

	else:
		types = r.json()

		if not(os.path.isdir(data_dir)):
			os.mkdir(data_dir)

		with open(os.path.join(data_dir, 'tfl_stop_types.json'), 'w') as f:
			f.write(json.dumps(types, ensure_ascii = False))
			print(f'Fetched {len(types)} valid stop types.')

def getStopCategories():
	try:
		r = retryRequest('https://api.tfl.gov.uk/StopPoint/Meta/categories')

	except Exception as err:
		print('Cannot fetch valid stop categories.')
		getStopCategories()

	else:
		_categories = r.json()
		categories = {}

		for _c in _categories:
			if _c['category'] not in categories:
				categories[_c['category']] = []
			if 'availableKeys' in _c:
				categories[_c['category']] = _c['availableKeys']

		if not(os.path.isdir(data_dir)):
			os.mkdir(data_dir)

		with open(os.path.join(data_dir, 'tfl_stop_categories.json'), 'w') as f:
			f.write(json.dumps(categories, ensure_ascii = False))
			print(f'Fetched {len(categories)} valid stop categories.')

def getRoutes():
	try:
		r = retryRequest('https://api.tfl.gov.uk/Line/Route')

	except Exception as err:
		print('Cannot fetch valid routes.')
		getRoutes()

	else:
		_routes = r.json()
		routes = {}
		
		for _route in _routes:
			if _route['id'] not in routes:
				routes[_route['id']] = {
					'name': _route['name'],
					'modeName': _route['modeName'],
					'disruptions': _route['disruptions'],
					'created': _route['created'],
					'modified': _route['modified'],
					'lineStatuses': _route['lineStatuses'],
					'routeSections': [],
					'serviceTypes': [],
					'crowding': []
				}

			for _route_section in _route['routeSections']:
				_route_section.pop('$type', None)
				routes[_route['id']]['routeSections'].append(_route_section)

			for _service_type in _route['serviceTypes']:
				_service_type.pop('$type', None)
				routes[_route['id']]['serviceTypes'].append(_service_type)

			_route['crowding'].pop('$type', None)
			routes[_route['id']]['crowding'] = _route['crowding']

		if not(os.path.isdir(data_dir)):
			os.mkdir(data_dir)

		with open(os.path.join(data_dir, 'tfl_routes.json'), 'w') as f:
			f.write(json.dumps(routes, ensure_ascii = False))
			print(f'Fetched {len(routes)} valid routes.')

def getRouteStops():
	with open(os.path.join(data_dir, 'tfl_routes.json'), 'r') as f:
		_routes = json.load(f)

		def getStopsFromEachRoute(id):
			# print(f'Now fetching route {id} ...')
			try:
				r = retryRequest(f'https://api.tfl.gov.uk/Line/{id}/Route/Sequence/all')

			except Exception as err:
				print(f'Cannot fetch valid route stops for {id}.')
				getStopsFromEachRoute(id)

			else:
				r = r.json()
				_line_strings = r['lineStrings']
				_stop_point_seqs = r['stopPointSequences']
				_ordered_line_routes = r['orderedLineRoutes']
				_details = {}

				if len(_line_strings) != len(_ordered_line_routes):
					print(f'0.1: Route {id} has mismatch section of lineStrings and orderedLineRoutes: {len(_line_strings)} vs {len(_ordered_line_routes)}')

				if id not in _details:
					_details[id] = {}
				if not r['isOutboundOnly']:
					_details[id]['inbound'] = {}
				_details[id]['outbound'] = {}

				for _seq in _stop_point_seqs:
					if _seq['branchId'] not in _details[id][_seq['direction']]:
						_details[id][_seq['direction']][_seq['branchId']] = []

					_stop_points = []
					_stop_letters = []
					# _name = []
					for _stop_point in _seq['stopPoint']:
						_stop_points.append(_stop_point['id'])
						if 'stopLetter' in _stop_point:
							_stop_letters.append(_stop_point['stopLetter'])
						else:
							_stop_letters.append('')
						# _name.append(_stop_point['name'])

					_details[id][_seq['direction']][_seq['branchId']].append({
						'prevBranchIds': _seq['prevBranchIds'],
						'nextBranchIds': _seq['nextBranchIds'],
						'stopPoint': _stop_points,
						'stopLetter': _stop_letters,
						# 'name': _name
					})

				with open(os.path.join(data_dir, 'temp.json'), 'w') as f:
					f.write(json.dumps(_details, ensure_ascii = False))

				def walkTree(branch, id, bound, branch_id, last_stop):
					# print('1.0: ', branch_id)

					if branch['nextBranchIds'] == []:
						# print('1.1: End of the branch - ', branch_id)
						
						if id not in details:
							details[id] = {}
						if bound not in details[id]:
							details[id][bound] = []

						_stop_points = []
						_stop_letters = []
						_names = []

						for i in branch_id:
							x = int(i.split('.')[0])
							y = int(i.split('.')[1])
							_stop_points += _details[id][bound][x][y]['stopPoint']
							_stop_letters += _details[id][bound][x][y]['stopLetter']
							# _names += _details[id][bound][x][y]['name']

						details[id][bound].append({
							'tree': branch_id,
							'stopPoint': _stop_points,
							'stopLetter': _stop_letters,
							# 'name': _names
						})

						return

					else:
						for next_branches in branch['nextBranchIds']:
							if next_branches in _details[id][bound]:
								for i in range(0, len(_details[id][bound][next_branches])):
									next_branch = _details[id][bound][next_branches][i]
									# print('1.1: ', bound, next_branches, next_branch['prevBranchIds'], next_branch['nextBranchIds'])

									# if next_branches in next_branch['prevBranchIds'] and next_branches in next_branch['nextBranchIds']:
									# 	print(f'1.1.1: Potential loop found on route {id} - ', bound, next_branch['prevBranchIds'], next_branches, next_branch['nextBranchIds'])

									# else:
									if last_stop == next_branch['stopPoint'][0]:
										# print('1.2: ', bound, next_branches, next_branch['prevBranchIds'], next_branch['nextBranchIds'])
										if 'isDeleted' not in next_branch:
											next_branch['stopPoint'].pop(0)
											next_branch['stopLetter'].pop(0)
											# next_branch['name'].pop(0)
											_details[id][bound][next_branches][i]['isDeleted'] = True
										
										branch_id.append(str(next_branches) + '.' + str(i))

										if loopDetect(branch_id):
											print(f'1.2.1: Loop found in tree {id}: {branch_id}')

										else:
											walkTree(next_branch, id, bound, list(branch_id), next_branch['stopPoint'][len(next_branch['stopPoint']) - 1])

				
				def loopDetect(nodes):
					if len(nodes) < 5:
						return False

					# print(nodes[-1], nodes[-3], nodes[-2], nodes[-4])
					if int(float(nodes[-1])) == int(float(nodes[-3])) and int(float(nodes[-2])) == int(float(nodes[-4])):
						return True

					return False
				details = {}
				for _details_k, _details_v in _details.items():
					for bound_k, bound_v in _details_v.items():
						for branch_k, branch_v in bound_v.items():
							for i in range(0, len(branch_v)):
								branch = branch_v[i]
								# print('0.1: ', bound_k, branch_k, branch['prevBranchIds'], branch['nextBranchIds'])

								if branch['prevBranchIds'] == []:
									# print('0.2: ', bound_k, branch_k, branch['prevBranchIds'], branch['nextBranchIds'])
									_branch_id = [str(branch_k) + '.' + str(i)]
									walkTree(branch, id, bound_k, list(_branch_id), branch['stopPoint'][len(branch['stopPoint']) - 1])
				
				with open(os.path.join(data_dir, 'temp2.json'), 'w') as f:
					f.write(json.dumps(details, ensure_ascii = False))

				return details

		details = [getStopsFromEachRoute(_id) for _id in _routes.keys()]

		with open(os.path.join(data_dir, 'tfl_route_details.json'), 'w') as f:
			f.write(json.dumps(details, ensure_ascii = False))
			print(f'Fetched {len(details)} valid route details.')

def _getStopsFromEachRoute(id):
	try:
		r = retryRequest(f'https://api.tfl.gov.uk/Line/{id}/Route/Sequence/all')

	except Exception as err:
		print(f'Cannot fetch valid route stops for {id}.')
		getStopsFromEachRoute(id)

	else:
		r = r.json()
		_line_strings = r['lineStrings']
		_stop_point_seqs = r['stopPointSequences']
		_ordered_line_routes = r['orderedLineRoutes']
		_details = {}

		if id not in _details:
			_details[id] = {}
		if not r['isOutboundOnly']:
			_details[id]['inbound'] = {}
		_details[id]['outbound'] = {}

		for _seq in _stop_point_seqs:
			if _seq['branchId'] not in _details[id][_seq['direction']]:
				_details[id][_seq['direction']][_seq['branchId']] = []

			_stop_points = []
			_stop_letters = []
			_name = []
			for _stop_point in _seq['stopPoint']:
				_stop_points.append(_stop_point['id'])
				if 'stopLetter' in _stop_point:
					_stop_letters.append(_stop_point['stopLetter'])
				else:
					_stop_letters.append('')
				_name.append(_stop_point['name'])

			_details[id][_seq['direction']][_seq['branchId']].append({
				'prevBranchIds': _seq['prevBranchIds'],
				'nextBranchIds': _seq['nextBranchIds'],
				'stopPoint': _stop_points,
				'stopLetter': _stop_letters,
				'name': _name
			})

		with open(os.path.join(data_dir, 'temp.json'), 'w') as f:
			f.write(json.dumps(_details, ensure_ascii = False))
			# print(f'Fetched {len(details)} valid route details.')

		def walkTree(branch, id, bound, branch_id, last_stop):
			print('1.0: ', branch_id)

			if branch['nextBranchIds'] == []:
				print('1.1: End of the branch - ', branch_id)
				
				if id not in details:
					details[id] = {}
				if bound not in details[id]:
					details[id][bound] = []

				_stop_points = []
				_stop_letters = []
				_names = []

				for _i, i in enumerate(branch_id):
					if _i == 0:
						continue

					x = int(i.split('.')[0])
					y = int(i.split('.')[1])
					_stop_points += _details[id][bound][x][y]['stopPoint']
					_stop_letters += _details[id][bound][x][y]['stopLetter']
					_names += _details[id][bound][x][y]['name']

				details[id][bound].append({
					'tree': branch_id,
					'stopPoint': _stop_points,
					'stopLetter': _stop_letters,
					'name': _names
				})

				return

			else:
				for next_branches in branch['nextBranchIds']:
					if next_branches in _details[id][bound]:
						for i in range(0, len(_details[id][bound][next_branches])):
							next_branch = _details[id][bound][next_branches][i]
							print('1.1: ', bound, next_branch['prevBranchIds'], next_branches, next_branch['nextBranchIds'])

							if next_branches in next_branch['prevBranchIds'] and next_branches in next_branch['nextBranchIds']:
								print(f'1.1.1: Potential loop found {id} - ', bound, next_branch['prevBranchIds'], next_branches, next_branch['nextBranchIds'])

							# else:
							if last_stop == next_branch['stopPoint'][0]:
								print('1.2: ', bound, next_branch['prevBranchIds'], next_branches, next_branch['nextBranchIds'])
								if 'isDeleted' not in next_branch:
									next_branch['stopPoint'].pop(0)
									next_branch['stopLetter'].pop(0)
									next_branch['name'].pop(0)
									_details[id][bound][next_branches][i]['isDeleted'] = True

								branch_id.append(str(next_branches) + '.' + str(i))
								print(branch_id)

								is_cycle = loopDetect(branch_id)

								if is_cycle:
									print(f'1.2.1: Loop found in tree {id}: {branch_id}')
									
								else:
									walkTree(next_branch, id, bound, list(branch_id), next_branch['stopPoint'][len(next_branch['stopPoint']) - 1])

		# def loopDetect(nodes):
		# 	class ListNode:
		# 		def __init__(self, value='', next=None):
		# 			self.value = value
		# 			self.next = next

		# 	def createLinkedList(nodes):
		# 		if not nodes:
		# 			return None

		# 		head = ListNode(nodes[0])
		# 		current = head

		# 		for value in nodes[1:]:
		# 			current.next = ListNode(value)
		# 			current = current.next

		# 		return head

		# 	def printLinkedList(head):
		# 		current = head

		# 		while current:
		# 			print(current.value, end=" -> ")
		# 			current = current.next

		# 		print("None")

		# 	def hasCycle(head):
		# 		slow, fast = head, head

		# 		while fast is not None and fast.next is not None:
		# 			slow = slow.next
		# 			fast = fast.next.next

		# 			if slow == fast:
		# 				print("fast meets slow at node", fast.value)
		# 				return True

		# 		return False

		# 	head = createLinkedList(nodes)
		# 	printLinkedList(head)

		# 	return hasCycle(head)

		def loopDetect(nodes):
			if len(nodes) < 5:
				return False

			# print(nodes[-1], nodes[-3], nodes[-2], nodes[-4])
			if int(float(nodes[-1])) == int(float(nodes[-3])) and int(float(nodes[-2])) == int(float(nodes[-4])):
				return True

			return False

		details = {}
		for _details_k, _details_v in _details.items():
			for bound_k, bound_v in _details_v.items():
				for branch_k, branch_v in bound_v.items():
					for i, branch in enumerate(branch_v):
						print('0.1: ', bound_k, branch['prevBranchIds'], branch_k, branch['nextBranchIds'])

						if len(branch['prevBranchIds']) == 0:
							print('0.2: Empty previous branch - ', bound_k, branch['prevBranchIds'], branch_k, branch['nextBranchIds'])
							_branch_id = ['-*.0', str(branch_k) + '.' + str(i)]
							walkTree(branch, id, bound_k, list(_branch_id), branch['stopPoint'][len(branch['stopPoint']) - 1])

						elif len(branch['prevBranchIds']) > 0 and i == len(branch_v) - 1:
							print('0.2: No previous branches are empty')
							branch = branch_v[0]
							for prev_branch in branch['prevBranchIds']:
								print('0.2.1: ', bound_k, branch['prevBranchIds'], branch_k, branch['nextBranchIds'])
								_branch_id = ['-' + str(prev_branch) + '.0', str(branch_k) + '.' + str(i)]
								walkTree(branch, id, bound_k, list(_branch_id), branch['stopPoint'][len(branch['stopPoint']) - 1])
								
		with open(os.path.join(data_dir, 'temp2.json'), 'w') as f:
			f.write(json.dumps(details, ensure_ascii = False))
			print(f'Fetched {len(details)} valid route details.')

def getStops():
	with open(os.path.join(data_dir, 'tfl_modes.json'), 'r') as f:
		_modes = json.load(f)

	_stops = {}

	for _mode in _modes.keys():
		while True:
			try:
				r = retryRequest(f'https://api.tfl.gov.uk/StopPoint/Mode/{_mode}?page=1')

			except Exception as err:
				print(f'Cannot fetch valid pagainations for stops from mode {_mode}.')
				continue

			break

		r = r.json()
		_page_size = r['pageSize']
		_total_count = r['total']
		if _page_size > 0 or _total_count > 0:
			_no_of_pages = math.ceil(_total_count / _page_size)
		else:
			_no_of_pages = -1
		print(_mode, _no_of_pages)

		if _no_of_pages > 0:


			for i in range(1, _no_of_pages + 1):
				while True:
					try:
						print(_mode, i, '/', _no_of_pages)
						r = retryRequest(f'https://api.tfl.gov.uk/StopPoint/Mode/{_mode}?page={i}')

					except Exception as err:
						print(f'Cannot fetch valid stops from page {i} of mode {_mode}.')
						continue

					break

				_results = r.json()['stopPoints']
				for _result in _results:
					if _result['id'] not in _stops:
						_stops[_result['id']] = []
					_stops[_result['id']].append(_result)

	def tidy(obj, target):
		if isinstance(obj, dict):
			for key in list(obj.keys()):
				if key == target:
					match target:
						case 'lines':
							_lines = {}
							for _line in obj[key]:
								if 'type' in _line and _line['type'] not in _lines:
									_lines[_line['type']] = []
								if 'id' in _line:
									_lines[_line['type']].append(_line['id'])

							obj[key] = _lines

						case 'lineModeGroups':
							_line_mode_groups = {}
							for _group in obj[key]:
								if 'modeName' in _group and _group['modeName'] not in _line_mode_groups:
									_line_mode_groups[_group['modeName']] = []
								if 'lineIdentifier' in _group:
									_line_mode_groups[_group['modeName']] = _group['lineIdentifier']

							obj[key] = _line_mode_groups

						case 'additionalProperties':
							_additional_properties = {}
							for _ap in obj[key]:
								if 'category' in _ap and _ap['category'] not in _additional_properties:
									_additional_properties[_ap['category']] = {}
								if 'key' in _ap and 'value' in _ap:
									_additional_properties[_ap['category']][_ap['key']] = _ap['value']

							obj[key] = _additional_properties

						case 'children':
							for _child in obj[key]:
								if 'children' in _child and len(_child['children']) > 0:
									for _c in _child['children']:
										if _c['id'] not in _stops:
											_stops[_c['id']] = []
										_stops[_c['id']].append(_c)
									
				else:
					tidy(obj[key], target)

		elif isinstance(obj, list):
			for i in reversed(range(len(obj))):
				if obj[i] == target:
					match target:
						case 'lines':
							_lines = {}
							for _line in obj[i]:
								if 'type' in _line and _line['type'] not in _lines:
									_lines[_line['type']] = []
								if 'id' in _line:
									_lines[_line['type']].append(_line['id'])

							obj[i] = _lines

						case 'lineModeGroups':
							_line_mode_groups = {}
							for _group in obj[key]:
								if 'modeName' in _group and _group['modeName'] not in _line_mode_groups:
									_line_mode_groups[_group['modeName']] = []
								if 'lineIdentifier' in _group:
									_line_mode_groups[_group['modeName']] = _group['lineIdentifier']

							obj[i] = _line_mode_groups

						case 'additionalProperties':
							_additional_properties = {}
							for _ap in obj[i]:
								if 'category' in _ap and _ap['category'] not in _additional_properties:
									_additional_properties[_ap['category']] = {}
								if 'key' in _ap and 'value' in _ap:
									_additional_properties[_ap['category']][_ap['key']] = _ap['value']

							obj[i] = _additional_properties

						case 'children':
							for _child in obj[i]:
								if 'children' in _child and len(_child['children']) > 0:
									for _c in _child['children']:
										if _c['id'] not in _stops:
											_stops[_c['id']] = []
										_stops[_c['id']].append(_c)

				else:
					tidy(obj[i], target)

		else:
			pass

	def count(obj, target, level):
		if isinstance(obj, dict):
			for key in list(obj.keys()):
				if key == target:
					tabs = ''
					if level > 0:
						for i in range(0, level):
							tabs += '\t'
					print(f'{tabs} Key: {obj["id"]}')
					level += 1
				count(obj[key], target, level)

		elif isinstance(obj, list):
			for i in reversed(range(len(obj))):
				if obj[i] == target:
					tabs = ''
					if level > 0:
						for i in range(0, level):
							tabs += '\t'
					print(f'tabs Value: {obj[i]["id"]}')
				count(obj[i], target, level)

		else:
			pass

	scrub(_stops, '$type')
	scrub(_stops, 'uri')
	scrub(_stops, 'sourceSystemKey')

	tidy(_stops, 'lines')
	tidy(_stops, 'lineModeGroups')
	tidy(_stops, 'additionalProperties')
	tidy(_stops, 'children')

	# print('\nBefore')
	# count(_stops, 'children', 0)

	for _s_key, _s_value in _stops.items():
		for _s in _s_value:
			if 'children' in _s:
				if len(_s['children']) == 0:
					del _s['children']
				else:
					_children = []
					for _c in _s['children']:
						_children.append(_c['id'])
					_s['children'] = _children

	# print('\nAfter')
	# count(_stops, 'children', 0)

	_geo = {
		'type': 'FeatureCollection',
		'features': []
	}

	for _stop_k, _stop_v in _stops.items():
		_merged = {}
		for _s in _stop_v:
			_merged = {**_merged, **_s}
			for _merged_k, _merged_v in _merged.items():
				if _merged_k in _merged and _merged_k in _s and _merged[_merged_k] != _s[_merged_k]:
					_merged[_merged_k] = [_merged_v, _merged[_merged_k]]
		_stops[_stop_k] = _merged

		_geo['features'].append({
			'type': 'Feature',
			'geometry': {
				'type': 'Point',
				'coordinates': [_stops[_stop_k]['lon'], _stops[_stop_k]['lat']]
			},
			'properties': _stops[_stop_k]
		})

	with open(os.path.join(data_dir, 'tfl_stops.json'), 'w') as f:
			f.write(json.dumps(_stops, ensure_ascii = False))
			print(f'Fetched {len(_stops)} valid stops.')

	with open(os.path.join(data_dir, 'tfl_stops_geo.json'), 'w') as f:
			f.write(json.dumps(_geo, ensure_ascii = False))
			print(f'Fetched {len(_geo)} valid stops.')

def main():
	print('Getting valid modes ...')
	getModes()

	print('Getting valid service types ...')
	getServiceTypes()

	print('Getting valid disruption categories ...')
	getDisruptionCategories()

	print('Getting valid severities ...')
	getSeverity()

	print('Getting valid stop types ...')
	getStopTypes()

	print('Getting valid stop categories ...')
	getStopCategories()

	print('Getting valid routes ...')
	getRoutes()

	print('Getting valid route stops ...')
	getRouteStops()
	
	print('Getting valid stop points ...')
	getStops()

	# _getStopsFromEachRoute('great-western-railway')
	# _getStopsFromEachRoute('metropolitan')
	# _getStopsFromEachRoute('b12')
	# _getStopsFromEachRoute('southeastern')

if __name__ == "__main__":
	main()

