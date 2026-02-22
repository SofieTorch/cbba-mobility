CREATE TABLE `lines` (
	`id` integer PRIMARY KEY NOT NULL,
	`name` text NOT NULL,
	`description` text,
	`status` text NOT NULL,
	`created_at` text NOT NULL,
	`updated_at` text NOT NULL,
	`cached_at` text NOT NULL
);
--> statement-breakpoint
CREATE TABLE `location_points` (
	`id` integer PRIMARY KEY AUTOINCREMENT NOT NULL,
	`recording_id` integer NOT NULL,
	`timestamp` text NOT NULL,
	`latitude` real NOT NULL,
	`longitude` real NOT NULL,
	`altitude` real,
	`speed` real,
	`bearing` real,
	`horizontal_accuracy` real,
	`vertical_accuracy` real,
	FOREIGN KEY (`recording_id`) REFERENCES `recordings`(`id`) ON UPDATE no action ON DELETE cascade
);
--> statement-breakpoint
CREATE TABLE `recordings` (
	`id` integer PRIMARY KEY AUTOINCREMENT NOT NULL,
	`server_id` integer,
	`status` text NOT NULL,
	`line_id` integer,
	`line_name` text,
	`direction` text,
	`device_model` text,
	`os_version` text,
	`notes` text,
	`started_at` text NOT NULL,
	`ended_at` text,
	`last_activity_at` text NOT NULL,
	`synced_at` text,
	`created_at` text NOT NULL
);
--> statement-breakpoint
CREATE TABLE `sensor_readings` (
	`id` integer PRIMARY KEY AUTOINCREMENT NOT NULL,
	`recording_id` integer NOT NULL,
	`timestamp` text NOT NULL,
	`accel_x` real,
	`accel_y` real,
	`accel_z` real,
	`gyro_x` real,
	`gyro_y` real,
	`gyro_z` real,
	`pressure` real,
	`magnetic_heading` real,
	FOREIGN KEY (`recording_id`) REFERENCES `recordings`(`id`) ON UPDATE no action ON DELETE cascade
);
