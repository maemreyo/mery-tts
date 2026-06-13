import type { InstallJobResponse } from "@api/generated/client";

export const installJobQueued: InstallJobResponse = {
  schema_version: "v1",
  job_id: "job-1",
  status: "queued",
};

export const installJobRunning: InstallJobResponse = {
  schema_version: "v1",
  job_id: "job-1",
  status: "running",
};

export const installJobSucceeded: InstallJobResponse = {
  schema_version: "v1",
  job_id: "job-1",
  status: "succeeded",
};

export const installJobFailed: InstallJobResponse = {
  schema_version: "v1",
  job_id: "job-1",
  status: "failed",
};

export const installJobCancelled: InstallJobResponse = {
  schema_version: "v1",
  job_id: "job-1",
  status: "cancelled",
};
