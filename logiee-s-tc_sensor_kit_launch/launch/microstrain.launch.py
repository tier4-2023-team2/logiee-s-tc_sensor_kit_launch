# Copyright 2020 Tier IV, Inc. All rights reserved.
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

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.actions import EmitEvent
from launch.actions import LogInfo
from launch.actions import RegisterEventHandler
from launch.conditions import IfCondition
from launch.event_handlers import OnProcessStart
from launch.events import matches_action
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import LifecycleNode
from launch_ros.event_handlers import OnStateTransition
from launch_ros.events import lifecycle
import lifecycle_msgs.msg


def generate_launch_description():

    # Node
    node = LifecycleNode(
        package="microstrain_inertial_driver",
        executable="microstrain_inertial_driver_node",
        namespace="",
        name="microstrain_inertial_driver_node",
        parameters=[
            {
                "port": LaunchConfiguration("port"),
                "baud_rate": LaunchConfiguration("baud_rate"),
                "debug": False,
                "diagnostics": True,
                "imu_frame_id": LaunchConfiguration("imu_frame_id"),
                "device_setup": True,
                "save_settings": True,
                "use_device_timestamp": False,
                "publish_imu": True,
                "imu_data_rate": LaunchConfiguration("imu_data_rate"),
            }
        ],
        output="screen",
    )

    # Take the 'configure' transition.
    configure_transition = RegisterEventHandler(
        event_handler=OnProcessStart(
            target_action=node,
            on_start=[
                # Log
                LogInfo(msg="start 'configuring'"),
                # Change State event
                EmitEvent(
                    event=lifecycle.ChangeState(
                        lifecycle_node_matcher=matches_action(node),
                        transition_id=lifecycle_msgs.msg.Transition.TRANSITION_CONFIGURE,
                    )
                ),
            ],
        ),
        condition=IfCondition(LaunchConfiguration("auto_configure")),
    )

    # When return to the 'unconfigured' state, Take the 'configure' transition again.
    reconfigure_transition = RegisterEventHandler(
        event_handler=OnStateTransition(
            target_lifecycle_node=node,
            goal_state="unconfigured",
            entities=[
                # Log
                LogInfo(msg="return to the 'unconfigured' state, start 'configuring' again"),
                # Change State event
                EmitEvent(
                    event=lifecycle.ChangeState(
                        lifecycle_node_matcher=matches_action(node),
                        transition_id=lifecycle_msgs.msg.Transition.TRANSITION_CONFIGURE,
                    )
                ),
            ],
        ),
        condition=IfCondition(LaunchConfiguration("auto_configure")),
    )

    # When reaches the 'inactive' state, take the 'activate' transition.
    activate_transition = RegisterEventHandler(
        event_handler=OnStateTransition(
            target_lifecycle_node=node,
            goal_state="inactive",
            entities=[
                # Log
                LogInfo(msg="reached the 'inactive' state, start 'activating'"),
                # Change State event
                EmitEvent(
                    event=lifecycle.ChangeState(
                        lifecycle_node_matcher=matches_action(node),
                        transition_id=lifecycle_msgs.msg.Transition.TRANSITION_ACTIVATE,
                    )
                ),
            ],
        ),
        condition=IfCondition(LaunchConfiguration("auto_activate")),
    )

    # When reaches the 'active' state, log a message.
    reached_active_state = RegisterEventHandler(
        OnStateTransition(
            target_lifecycle_node=node,
            goal_state="active",
            entities=[
                LogInfo(msg="reached the 'active' state"),
            ],
        )
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument("port", default_value="/dev/ttyACM0"),
            DeclareLaunchArgument("baud_rate", default_value="115200"),
            DeclareLaunchArgument("imu_frame_id", default_value="imu_link"),
            DeclareLaunchArgument("imu_data_rate", default_value="100"),
            DeclareLaunchArgument("auto_configure", default_value="true"),
            DeclareLaunchArgument("auto_activate", default_value="true"),
            node,
            configure_transition,
            reconfigure_transition,
            activate_transition,
            reached_active_state,
        ]
    )
