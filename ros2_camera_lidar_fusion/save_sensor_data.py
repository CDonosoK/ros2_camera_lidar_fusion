#!/usr/bin/env python3

import rclpy, os, cv2, datetime

import numpy as np
from cv_bridge import CvBridge
import open3d as o3d

from rclpy.node import Node
from sensor_msgs.msg import Image, PointCloud2
from sensor_msgs_py import point_cloud2


from message_filters import Subscriber, ApproximateTimeSynchronizer

class SensorFusionNode(Node):
    def __init__(self):
        super().__init__('sensor_fusion_node')
        self.get_logger().info('Sensor Fusion Node has been started')

        self.image_sub = Subscriber(
            self,
            Image,
            '/pcl_human_segmentation/camera/raw_image'
        )
        self.pointcloud_sub = Subscriber(
            self,
            PointCloud2,
            '/rslidar_points'
        )

        self.max_file_saved = 10
        self.storage_path = '/ros2_ws/src/ros2_pcl_segmentation/pcl_camera_lidar_fusion/data'
        if not os.path.exists(self.storage_path):
            os.makedirs(self.storage_path)

        self.ts = ApproximateTimeSynchronizer(
            [self.image_sub, self.pointcloud_sub],
            queue_size=10,
            slop=0.1
        )
        
        self.ts.registerCallback(self.synchronize_data)

    def synchronize_data(self, image_msg, pointcloud_msg):
        file_name = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        self.get_logger().info(f'Synchronizing data at {file_name}')
        total_files = len(os.listdir(self.storage_path))
        if total_files <= self.max_file_saved:
            self.save_data(image_msg, pointcloud_msg, file_name)

    def pointcloud2_to_open3d(self, pointcloud_msg):
        points = []
        for p in point_cloud2.read_points(pointcloud_msg, skip_nans=True):
            points.append([p[0], p[1], p[2]])
        pointcloud = o3d.geometry.PointCloud()
        pointcloud.points = o3d.utility.Vector3dVector(np.array(points, dtype=np.float32))
        return pointcloud


    def save_data(self, image_msg, pointcloud_msg, file_name):
        bridge = CvBridge()
        image = bridge.imgmsg_to_cv2(image_msg, 'bgr8')
        pointcloud = self.pointcloud2_to_open3d(pointcloud_msg)
        o3d.io.write_point_cloud(f'{self.storage_path}/{file_name}.pcd', pointcloud)
        cv2.imwrite(f'{self.storage_path}/{file_name}.png', image)
        self.get_logger().info(f'Data has been saved at {self.storage_path}/{file_name}.png')



def main(args=None):
    rclpy.init(args=args)
    node = SensorFusionNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()