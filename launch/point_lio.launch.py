import os.path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch.substitutions import PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def _livox_driver_node():
    livox_config_path = os.path.join(
        get_package_share_directory("livox_ros_driver2"),
        "config",
        "MID360_config.json",
    )

    return Node(
        package="livox_ros_driver2",
        executable="livox_ros_driver2_node",
        name="livox_lidar_publisher",
        output="screen",
        parameters=[
            {"xfer_format": 1},
            {"multi_topic": 0},
            {"data_src": 0},
            {"publish_freq": 10.0},
            {"output_data_type": 0},
            {"frame_id": "livox_frame"},
            {"lvx_file_path": "/home/livox/livox_test.lvx"},
            {"user_config_path": livox_config_path},
            {"cmdline_input_bd_code": "livox0000000001"},
        ],
    )


def generate_launch_description():
    use_sim_time = LaunchConfiguration("use_sim_time")
    map_save_path = LaunchConfiguration("map_save_path")

    r2_description_launch = PathJoinSubstitution(
        [
            FindPackageShare("r2_spawner"),
            "launch",
            "description.launch.py",
        ]
    )
    point_lio_config = PathJoinSubstitution(
        [
            FindPackageShare("point_lio"),
            "config",
            "mid360.yaml",
        ]
    )
    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "use_sim_time",
                default_value="false",
                description="Use simulation clock if true.",
            ),
            DeclareLaunchArgument(
                "map_save_path",
                default_value="/tmp/point_lio_r2_map.pcd",
                description="PCD path written by /map_save.",
            ),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(r2_description_launch),
                launch_arguments={"use_sim_time": use_sim_time}.items(),
            ),
            _livox_driver_node(),
            Node(
                package="cpp_lidar_filter",
                executable="lidar_filter_node",
                name="lidar_filter_node",
                output="screen",
                parameters=[
                    {
                        "use_sim_time": use_sim_time,
                        "output_topic": "",
                        "livox_output_topic": "",
                        "point_lio_output_topic": "/livox/lidar_filtered_pointlio",
                    }
                ],
            ),
            Node(
                package="point_lio",
                executable="pointlio_mapping",
                name="laserMapping",
                output="screen",
                parameters=[
                    point_lio_config,
                    {
                        "use_sim_time": use_sim_time,
                        "use_imu_as_input": False,
                        "prop_at_freq_of_imu": True,
                        "check_satu": True,
                        "init_map_size": 10,
                        "point_filter_num": 1,
                        "space_down_sample": True,
                        "filter_size_surf": 0.1,
                        "filter_size_map": 0.3,
                        "cube_side_length": 1000.0,
                        "runtime_pos_log_enable": False,
                        "odom_header_frame_id": "odom",
                        "odom_child_frame_id": "point_lio_body",
                        "publish_tf": False,
                    },
                ],
                remappings=[
                    ("/aft_mapped_to_init", "/point_lio/aft_mapped_to_init_raw"),
                    ("/cloud_registered", "/point_lio/cloud_registered_raw"),
                    ("/Laser_map", "/point_lio/Laser_map_raw"),
                ],
            ),
            Node(
                package="cpp_lidar_filter",
                executable="point_lio_compat_node",
                name="point_lio_compat_node",
                output="screen",
                parameters=[
                    {
                        "use_sim_time": use_sim_time,
                        "raw_odom_topic": "/point_lio/aft_mapped_to_init_raw",
                        "raw_cloud_topic": "/point_lio/cloud_registered_raw",
                        "odom_topic": "/Odometry",
                        "cloud_topic": "/cloud_registered",
                        "cloud_map_topic": "/cloud_map",
                        "odom_frame": "odom",
                        "base_frame": "base_link",
                        "body_frame": "imu_link",
                        "save_pcd": False,
                        "enable_cloud_map": False,
                        "enable_map_save_service": False,
                        "map_save_path": map_save_path,
                    }
                ],
            ),
        ]
    )
