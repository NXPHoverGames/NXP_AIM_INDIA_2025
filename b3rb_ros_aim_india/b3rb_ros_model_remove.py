# Copyright 2025 NXP

# Copyright 2016 Open Source Robotics Foundation, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import rclpy
from rclpy.node import Node
from rclpy.parameter import Parameter

import re
import subprocess as sp
from synapse_msgs.msg import WarehouseShelf

QOS_PROFILE_DEFAULT = 10
REMOVE_CMD = """gz service -s /world/default/remove --reqtype gz.msgs.Entity --reptype gz.msgs.Boolean --req 'type: MODEL; name: "curtain_"""

QR_CODE_LIST = ["1_315.0_Ad5PqIlXvPqApGFdLXEboS",
		"2_000.0_HKq3wvCg8DGyflz3oNIj8d",]  # warehouse_1.


def extract_integer(qr_string: str):
	if not isinstance(qr_string, str):
		return None

	match = re.match(r'(\d+)_', qr_string)
	if match:
		return int(match.group(1))
	else:
		return None


class ModelRemover(Node):
	def __init__(self):
		super().__init__('model_remover')

		self.subscription_shelf_data = self.create_subscription(
			WarehouseShelf,
			'/shelf_data',
			self.shelf_data_callback,
			QOS_PROFILE_DEFAULT)

		self.num_shelves = len(QR_CODE_LIST)
		self.shelf_reached = [False] * (self.num_shelves)
		self.highest_revealed_shelf = 1

	def shelf_data_callback(self, msg: WarehouseShelf):
		if msg.qr_decoded not in QR_CODE_LIST:
			return

		shelf_id = extract_integer(msg.qr_decoded)

		if shelf_id is None:
			return

		if shelf_id == self.num_shelves:
			return

		self.shelf_reached[shelf_id] = True

		contiguous_reached_up_to = 0
		for i in range(1, self.num_shelves):
			if self.shelf_reached[i] is True:
				contiguous_reached_up_to = i
			else:
				break

		for i in range(self.highest_revealed_shelf, contiguous_reached_up_to + 1):
			curtain_remove = str(i + 1)

			command = REMOVE_CMD + curtain_remove + """"'"""
			result = sp.run(command, shell=True, check=True,
						stdout=sp.PIPE, stderr=sp.PIPE)

			self.highest_revealed_shelf = i + 1


def main(args=None):
	rclpy.init(args=args)

	model_remover = ModelRemover()

	rclpy.spin(model_remover)

	# Destroy the node explicitly
	# (optional - otherwise it will be done automatically
	# when the garbage collector destroys the node object)
	model_remover.destroy_node()
	rclpy.shutdown()


if __name__ == '__main__':
	main()
