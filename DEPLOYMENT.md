# Deployment Guide for Plugus on Render

This guide explains how to deploy the Plugus application to [Render](https://render.com) using the configurations we've set up.

## Prerequisites
- A GitHub account with this repository pushed.
- A [Render](https://render.com) account.

## Deployment Steps

1.  **Log in to Render** and go to your Dashboard.
2.  Click **New +** and select **Blueprint**.
3.  Connect your GitHub repository (`https://github.com/lavdeep2332/Plugus-app`).
4.  Render will automatically detect the `render.yaml` file.
5.  **Review the resources**:
    - `plugus-db` (Database)
    - `plugus-redis` (Redis)
    - `plugus-backend` (Web Service)
    - `plugus-frontend` (Static Site)
6.  Click **Apply**. Render will start creating the resources.

## Post-Deployment Configuration

### Frontend API URL
The `render.yaml` file has a placeholder for the frontend to know where the backend is.
1.  Wait for the `plugus-backend` service to be live.
2.  Copy its URL (e.g., `https://plugus-backend-xyz.onrender.com`).
3.  Go to the **plugus-frontend** service in Render Dashboard.
4.  Go to **Environment**.
5.  Add/Edit the environment variable:
    - Key: `EXPO_PUBLIC_API_URL`
    - Value: `https://plugus-backend-xyz.onrender.com/api/v1` (Append `/api/v1`)
6.  **Save Changes** and **Deploy Latest Commit** (or `Clear Build Cache & Deploy`) to rebuild the frontend with the correct URL.

## Important Notes
- **Database Persistence**: The free tier PostgreSQL database on Render expires after 90 days. For production, upgrade to a paid managed database.
- **Cold Starts**: Free tier web services spin down after inactivity. The first request might take 50+ seconds.
