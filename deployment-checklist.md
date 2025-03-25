# aeaiou API Deployment Checklist

## Pre-Deployment Tasks

- [ ] Set up an AWS account if you haven't already (for S3 storage)
- [ ] Create an S3 bucket named `aeaiou-images` with public read access
- [ ] Get a Replicate API token from [replicate.com/account/api-tokens](https://replicate.com/account/api-tokens)
- [ ] Configure your server with Docker and Docker Compose
- [ ] Ensure your domain (aeaiou.com) points to your server's IP address

## Server Setup

1. SSH into your server:
   ```
   ssh user@your-server-ip
   ```

2. Create a directory for the application:
   ```
   mkdir -p /var/www/aeaiou
   cd /var/www/aeaiou
   ```

3. Clone your repository:
   ```
   git clone https://github.com/moondin/aeaiou.git .
   ```

4. Create the .env file:
   ```
   cp production.env.template .env
   nano .env  # Edit with your actual credentials
   ```

5. Create necessary directories:
   ```
   mkdir -p storage
   mkdir -p certbot/conf
   mkdir -p certbot/www
   ```

## Deployment

1. Start the services using Docker Compose:
   ```
   docker-compose -f docker-compose.prod.yml up -d
   ```

2. Set up SSL certificates with Let's Encrypt:
   ```
   docker-compose -f docker-compose.prod.yml run --rm certbot certonly \
     --webroot --webroot-path=/var/www/certbot \
     --email your-email@example.com --agree-tos --no-eff-email \
     -d aeaiou.com -d www.aeaiou.com
   ```

3. Restart Nginx to apply SSL certificates:
   ```
   docker-compose -f docker-compose.prod.yml restart nginx
   ```

## Verification

1. Check if all containers are running:
   ```
   docker-compose -f docker-compose.prod.yml ps
   ```

2. View logs for any errors:
   ```
   docker-compose -f docker-compose.prod.yml logs -f api
   ```

3. Test the API endpoints:
   ```
   curl https://aeaiou.com/api/v1/health
   ```

## Monitoring Setup

1. Set up basic monitoring with Docker stats:
   ```
   docker stats
   ```

2. For more advanced monitoring, consider setting up:
   - Prometheus + Grafana for metrics
   - ELK Stack for log management
   - Uptime Robot for availability monitoring

## Backup Strategy

1. Set up automated backups for:
   - Redis data: `/var/www/aeaiou/redis-data`
   - SSL certificates: `/var/www/aeaiou/certbot/conf`
   
2. Configure S3 bucket versioning for your images

## Security Measures

1. Set up a firewall allowing only necessary ports:
   ```
   ufw allow 80
   ufw allow 443
   ufw allow 22
   ufw enable
   ```

2. Configure fail2ban to prevent brute force attempts:
   ```
   apt-get install fail2ban
   service fail2ban start
   ```

3. Set up automatic security updates:
   ```
   apt-get install unattended-upgrades
   dpkg-reconfigure -plow unattended-upgrades
   ```

## Maintenance Plan

1. Set up a weekly maintenance schedule:
   - Check logs for errors
   - Update dependencies
   - Run security scans
   - Verify backups

2. Create an update procedure:
   ```
   cd /var/www/aeaiou
   git pull
   docker-compose -f docker-compose.prod.yml build
   docker-compose -f docker-compose.prod.yml up -d
   ```
