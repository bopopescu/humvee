# -*- coding: utf-8 -*- #
# Copyright 2018 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Utility functions for Google Compute Engine resource policies."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core import yaml
from googlecloudsdk.core.util import times


_API_TIMEZONE = times.UTC


def _ParseWeeklyDayAndTime(start_time, weekday):
  """Converts the dt and day to _API_TIMEZONE and returns API formatted values.

  Args:
    start_time: The datetime object which represents a start time.
    weekday: The times.Weekday value which corresponds to the weekday.

  Returns:
    The weekday and start_time pair formatted as strings for use by the API
    clients.
  """
  weekday = times.GetWeekdayInTimezone(start_time, weekday, _API_TIMEZONE)
  formatted_time = _FormatStartTime(start_time)
  return weekday.name, formatted_time


def _FormatStartTime(dt):
  return times.FormatDateTime(dt, '%H:%M', _API_TIMEZONE)


def MakeVmMaintenancePolicy(policy_ref, args, messages):
  """Creates a VM Maintenance Window Resource Policy message from args."""
  _, daily_cycle, weekly_cycle = _ParseCycleFrequencyArgs(args, messages)
  vm_policy = messages.ResourcePolicyVmMaintenancePolicy(
      maintenanceWindow=
      messages.ResourcePolicyVmMaintenancePolicyMaintenanceWindow(
          dailyMaintenanceWindow=daily_cycle,
          weeklyMaintenanceWindow=weekly_cycle))
  return messages.ResourcePolicy(
      name=policy_ref.Name(),
      description=args.description,
      region=policy_ref.region,
      vmMaintenancePolicy=vm_policy)


def MakeDiskBackupSchedulePolicy(policy_ref, args, messages):
  """Creates a Disk Snapshot Schedule Resource Policy message from args."""
  hourly_cycle, daily_cycle, weekly_cycle = _ParseCycleFrequencyArgs(
      args, messages, supports_hourly=True)

  snapshot_properties = None
  snapshot_labels = labels_util.ParseCreateArgs(
      args,
      messages.ResourcePolicyBackupSchedulePolicySnapshotProperties.LabelsValue,
      labels_dest='snapshot_labels')
  storage_location = [args.storage_location] if args.storage_location else []
  if (args.IsSpecified('guest_flush') or snapshot_labels or storage_location):
    snapshot_properties = (
        messages.ResourcePolicyBackupSchedulePolicySnapshotProperties(
            guestFlush=args.guest_flush,
            labels=snapshot_labels,
            storageLocations=storage_location))
  backup_policy = messages.ResourcePolicyBackupSchedulePolicy(
      retentionPolicy=
      messages.ResourcePolicyBackupSchedulePolicyRetentionPolicy(
          maxRetentionDays=args.max_retention_days),
      schedule=messages.ResourcePolicyBackupSchedulePolicySchedule(
          hourlySchedule=hourly_cycle,
          dailySchedule=daily_cycle,
          weeklySchedule=weekly_cycle),
      snapshotProperties=snapshot_properties)
  return messages.ResourcePolicy(
      name=policy_ref.Name(),
      description=args.description,
      region=policy_ref.region,
      backupSchedulePolicy=backup_policy)


def _ParseCycleFrequencyArgs(args, messages, supports_hourly=False):
  """Parses args and returns a tuple of DailyCycle and WeeklyCycle messages."""
  _ValidateCycleFrequencyArgs(args)

  hourly_cycle, daily_cycle, weekly_cycle = None, None, None
  if args.daily_cycle:
    daily_cycle = messages.ResourcePolicyDailyCycle(
        daysInCycle=1,
        startTime=_FormatStartTime(args.start_time))
  if args.weekly_cycle:
    day_enum = messages.ResourcePolicyWeeklyCycleDayOfWeek.DayValueValuesEnum
    weekday = times.Weekday.Get(args.weekly_cycle.upper())
    day, start_time = _ParseWeeklyDayAndTime(args.start_time, weekday)
    weekly_cycle = messages.ResourcePolicyWeeklyCycle(
        dayOfWeeks=[
            messages.ResourcePolicyWeeklyCycleDayOfWeek(
                day=day_enum(day),
                startTime=start_time)])
  if args.IsSpecified('weekly_cycle_from_file'):
    if args.weekly_cycle_from_file:
      weekly_cycle = _ParseWeeklyCycleFromFile(args, messages)
    else:
      raise exceptions.InvalidArgumentException(
          args.GetFlag('weekly_cycle_from_file'), 'File cannot be empty.')
  if supports_hourly and args.hourly_cycle:
    hourly_cycle = messages.ResourcePolicyHourlyCycle(
        hoursInCycle=args.hourly_cycle,
        startTime=_FormatStartTime(args.start_time))
  return hourly_cycle, daily_cycle, weekly_cycle


def _ValidateCycleFrequencyArgs(args):
  """Validates cycle frequency args."""
  if args.IsSpecified('daily_cycle') and not args.daily_cycle:
    raise exceptions.InvalidArgumentException(
        args.GetFlag('daily_cycle'), 'cannot request a non-daily cycle.')


def _ParseWeeklyCycleFromFile(args, messages):
  """Parses WeeklyCycle message from file contents specified in args."""
  weekly_cycle_dict = yaml.load(args.weekly_cycle_from_file)
  day_enum = messages.ResourcePolicyWeeklyCycleDayOfWeek.DayValueValuesEnum
  days_of_week = []
  for day_and_time in weekly_cycle_dict:
    if 'day' not in day_and_time or 'startTime' not in day_and_time:
      raise exceptions.InvalidArgumentException(
          args.GetFlag('weekly_cycle_from_file'),
          'Each JSON/YAML object in the list must have the following keys: '
          '[day, startTime].')
    day = day_and_time['day'].upper()
    try:
      weekday = times.Weekday.Get(day)
    except KeyError:
      raise exceptions.InvalidArgumentException(
          args.GetFlag('weekly_cycle_from_file'),
          'Invalid value for `day`: [{}].'.format(day))
    start_time = arg_parsers.Datetime.Parse(day_and_time['startTime'])
    day, start_time = _ParseWeeklyDayAndTime(start_time, weekday)
    days_of_week.append(
        messages.ResourcePolicyWeeklyCycleDayOfWeek(
            day=day_enum(day),
            startTime=start_time))
  return messages.ResourcePolicyWeeklyCycle(dayOfWeeks=days_of_week)


def ParseResourcePolicy(resources, name, project=None, region=None):
  return resources.Parse(
      name, {'project': project, 'region': region},
      collection='compute.resourcePolicies')


def ParseResourcePolicyWithZone(resources, name, project, zone):
  region = utils.ZoneNameToRegionName(zone)
  return ParseResourcePolicy(resources, name, project, region)