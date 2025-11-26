import boto3
from boto3.dynamodb.conditions import Key
from typing import List, Dict, Any, Optional
import os
import uuid
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()


class DynamoDBService:
    def __init__(self):
        self.dynamodb = None
        self.table_name = 'TermsAndConditions'
        self._table = None
        self._initialized = False

    def _get_dynamodb(self):
        """Lazy initialize DynamoDB resource"""
        if self.dynamodb is None:
            self.dynamodb = boto3.resource(
                'dynamodb',
                region_name='us-west-2',
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
                aws_session_token=os.getenv('AWS_SESSION_TOKEN')
            )
        return self.dynamodb

    @property
    def table(self):
        """Lazy initialize table"""
        if self._table is None:
            self._ensure_table_exists()
        return self._table

    def _ensure_table_exists(self):
        """Create table if it doesn't exist"""
        try:
            self._table = self._get_dynamodb().Table(self.table_name)
            self._table.load()
        except self._get_dynamodb().meta.client.exceptions.ResourceNotFoundException:
            # Create table
            self._table = self._get_dynamodb().create_table(
                TableName=self.table_name,
                KeySchema=[
                    {'AttributeName': 'id', 'KeyType': 'HASH'}
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'id', 'AttributeType': 'S'}
                ],
                BillingMode='PAY_PER_REQUEST'
            )
            self._table.wait_until_exists()
        except Exception as e:
            # Re-raise with better error message
            raise Exception(f"Failed to connect to DynamoDB: {e}. Make sure AWS credentials are set.")

    def get_all_companies(self) -> List[Dict[str, Any]]:
        """Get all companies from the database"""
        response = self.table.scan()
        items = response.get('Items', [])

        # Handle pagination
        while 'LastEvaluatedKey' in response:
            response = self.table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            items.extend(response.get('Items', []))

        return items

    def get_company(self, company_id: str) -> Optional[Dict[str, Any]]:
        """Get a single company by ID"""
        response = self.table.get_item(Key={'id': company_id})
        return response.get('Item')

    def create_company(self, name: str, category: str, terms_text: str,
                       terms_risks: List[Dict] = None, terms_summary: str = None,
                       icon_url: str = None, cookie_text: str = None,
                       cookie_summary: str = None, cookie_risks: List[Dict] = None,
                       privacy_text: str = None, privacy_summary: str = None,
                       privacy_risks: List[Dict] = None) -> Dict[str, Any]:
        """Create a new company entry"""
        company_id = str(uuid.uuid4())

        item = {
            'id': company_id,
            'name': name,
            'category': category,
            'icon_url': icon_url or '',
            'last_updated': datetime.utcnow().isoformat(),
            # Terms and conditions fields
            'terms_text': terms_text,
            'terms_summary': terms_summary or '',
            'terms_risks': terms_risks or [],
            # Cookie policy fields
            'cookie_text': cookie_text or '',
            'cookie_summary': cookie_summary or '',
            'cookie_risks': cookie_risks or [],
            # Privacy policy fields
            'privacy_text': privacy_text or '',
            'privacy_summary': privacy_summary or '',
            'privacy_risks': privacy_risks or []
        }

        self.table.put_item(Item=item)
        return item

    def update_company_analysis(self, company_id: str, terms_risks: List[Dict], terms_summary: str) -> bool:
        """Update company with T&C analysis results"""
        try:
            self.table.update_item(
                Key={'id': company_id},
                UpdateExpression='SET terms_risks = :r, terms_summary = :s, last_updated = :u',
                ExpressionAttributeValues={
                    ':r': terms_risks,
                    ':s': terms_summary,
                    ':u': datetime.utcnow().isoformat()
                }
            )
            return True
        except Exception as e:
            print(f"Error updating company: {e}")
            return False

    def update_cookie_text(self, company_id: str, cookie_text: str) -> bool:
        """Update company with cookie policy text"""
        try:
            self.table.update_item(
                Key={'id': company_id},
                UpdateExpression='SET cookie_text = :ct, last_updated = :u',
                ExpressionAttributeValues={
                    ':ct': cookie_text,
                    ':u': datetime.utcnow().isoformat()
                }
            )
            return True
        except Exception as e:
            print(f"Error updating cookie text: {e}")
            return False

    def update_company_cookie_analysis(self, company_id: str, cookie_risks: List[Dict], cookie_summary: str) -> bool:
        """Update company with cookie policy analysis results"""
        try:
            self.table.update_item(
                Key={'id': company_id},
                UpdateExpression='SET cookie_risks = :cr, cookie_summary = :cs, last_updated = :u',
                ExpressionAttributeValues={
                    ':cr': cookie_risks,
                    ':cs': cookie_summary,
                    ':u': datetime.utcnow().isoformat()
                }
            )
            return True
        except Exception as e:
            print(f"Error updating cookie analysis: {e}")
            return False

    def update_privacy_text(self, company_id: str, privacy_text: str) -> bool:
        """Update company with privacy policy text"""
        try:
            self.table.update_item(
                Key={'id': company_id},
                UpdateExpression='SET privacy_text = :pt, last_updated = :u',
                ExpressionAttributeValues={
                    ':pt': privacy_text,
                    ':u': datetime.utcnow().isoformat()
                }
            )
            return True
        except Exception as e:
            print(f"Error updating privacy text: {e}")
            return False

    def update_company_privacy_analysis(self, company_id: str, privacy_risks: List[Dict], privacy_summary: str) -> bool:
        """Update company with privacy policy analysis results"""
        try:
            self.table.update_item(
                Key={'id': company_id},
                UpdateExpression='SET privacy_risks = :pr, privacy_summary = :ps, last_updated = :u',
                ExpressionAttributeValues={
                    ':pr': privacy_risks,
                    ':ps': privacy_summary,
                    ':u': datetime.utcnow().isoformat()
                }
            )
            return True
        except Exception as e:
            print(f"Error updating privacy analysis: {e}")
            return False

    def delete_company(self, company_id: str) -> bool:
        """Delete a company"""
        try:
            self.table.delete_item(Key={'id': company_id})
            return True
        except Exception:
            return False

    def migrate_schema(self) -> Dict[str, Any]:
        """
        Migration: Rename old fields to new naming convention.
        - 'risks' → 'terms_risks'
        - 'summary' → 'terms_summary'
        Also initializes new fields (privacy_*, cookie_*) if missing.
        Safe to run multiple times - only updates what needs updating.
        """
        companies = self.get_all_companies()
        migrated = 0
        skipped = 0
        errors = []

        for company in companies:
            company_id = company.get('id')
            needs_update = False
            update_expr_parts = []
            remove_parts = []
            expr_values = {':u': datetime.utcnow().isoformat()}

            # Migrate risks → terms_risks
            if 'risks' in company:
                update_expr_parts.append('terms_risks = :tr')
                expr_values[':tr'] = company.get('risks', [])
                remove_parts.append('risks')
                needs_update = True
            elif 'terms_risks' not in company:
                update_expr_parts.append('terms_risks = :tr')
                expr_values[':tr'] = []
                needs_update = True

            # Migrate summary → terms_summary
            if 'summary' in company:
                update_expr_parts.append('terms_summary = :ts')
                expr_values[':ts'] = company.get('summary', '')
                remove_parts.append('summary')
                needs_update = True
            elif 'terms_summary' not in company:
                update_expr_parts.append('terms_summary = :ts')
                expr_values[':ts'] = ''
                needs_update = True

            # Initialize cookie fields if missing
            if 'cookie_text' not in company:
                update_expr_parts.append('cookie_text = :ct')
                expr_values[':ct'] = ''
                needs_update = True
            if 'cookie_summary' not in company:
                update_expr_parts.append('cookie_summary = :cs')
                expr_values[':cs'] = ''
                needs_update = True
            if 'cookie_risks' not in company:
                update_expr_parts.append('cookie_risks = :cr')
                expr_values[':cr'] = []
                needs_update = True

            # Initialize privacy fields if missing
            if 'privacy_text' not in company:
                update_expr_parts.append('privacy_text = :pt')
                expr_values[':pt'] = ''
                needs_update = True
            if 'privacy_summary' not in company:
                update_expr_parts.append('privacy_summary = :ps')
                expr_values[':ps'] = ''
                needs_update = True
            if 'privacy_risks' not in company:
                update_expr_parts.append('privacy_risks = :pr')
                expr_values[':pr'] = []
                needs_update = True

            if not needs_update:
                skipped += 1
                continue

            try:
                # Build update expression
                update_expr_parts.append('last_updated = :u')
                update_expr = 'SET ' + ', '.join(update_expr_parts)
                if remove_parts:
                    update_expr += ' REMOVE ' + ', '.join(remove_parts)

                self.table.update_item(
                    Key={'id': company_id},
                    UpdateExpression=update_expr,
                    ExpressionAttributeValues=expr_values
                )
                migrated += 1
            except Exception as e:
                errors.append(f"{company.get('name', company_id)}: {str(e)}")

        return {
            'migrated': migrated,
            'skipped': skipped,
            'total': len(companies),
            'errors': errors
        }

    def seed_sample_data(self) -> List[Dict[str, Any]]:
        """Seed database with sample companies"""
        sample_companies = [
            {
                'name': 'Facebook',
                'category': 'social',
                'icon_url': 'https://upload.wikimedia.org/wikipedia/commons/5/51/Facebook_f_logo_%282019%29.svg',
                'terms_text': '''Facebook Terms of Service Summary:

1. Data Collection: We collect information you provide, content you create, and information about your connections and interactions.

2. Data Sharing: We share data with third-party partners, advertisers, and within the Meta family of companies.

3. Content License: You grant us a non-exclusive, transferable, sub-licensable, royalty-free, worldwide license to use your content.

4. Advertising: We use your data to show you personalized ads. You cannot opt out of ads entirely.

5. Account Termination: We can terminate or suspend your account at any time for any reason.

6. Arbitration: Disputes must be resolved through binding arbitration, not courts.

7. Location Tracking: We collect precise location data from your device.

8. Cross-Platform Tracking: We track your activity across websites and apps that use our services.'''
            },
            {
                'name': 'TikTok',
                'category': 'social',
                'icon_url': 'https://upload.wikimedia.org/wikipedia/en/a/a9/TikTok_logo.svg',
                'terms_text': '''TikTok Terms of Service Summary:

1. Data Collection: We collect device info, content, messages, metadata, and behavioral data.

2. Content Rights: You grant TikTok an unconditional, irrevocable, non-exclusive, royalty-free, fully transferable license to use your content anywhere, forever.

3. Data Sharing: We share data with business partners, advertisers, and potentially government entities.

4. Algorithm Training: Your content and interactions may be used to train our recommendation algorithms.

5. Age Requirements: Users must be 13+ (16+ in some regions), but enforcement is limited.

6. Biometric Data: We may collect faceprints and voiceprints from your content.

7. Clipboard Access: The app may access your device clipboard.

8. Account Deletion: We may retain your data even after account deletion.'''
            },
            {
                'name': 'Tinder',
                'category': 'dating',
                'icon_url': 'https://upload.wikimedia.org/wikipedia/commons/e/e6/Tinder_logo.svg',
                'terms_text': '''Tinder Terms of Service Summary:

1. Profile Data: We collect photos, bio, preferences, location, and communication content.

2. Payment Information: Premium features require payment details which we store.

3. Background Checks: We may conduct background checks on users.

4. Data Retention: Your data may be kept for years after account deletion.

5. Third-Party Sharing: We share data with Match Group companies and external partners.

6. Location Tracking: Continuous location tracking for matching and safety features.

7. Message Monitoring: We may review your messages for safety and policy compliance.

8. Photo Analysis: We analyze your photos using facial recognition and AI.'''
            },
            {
                'name': 'X',
                'category': 'social',
                'icon_url': 'https://upload.wikimedia.org/wikipedia/commons/c/ce/X_logo_2023.svg',
                'terms_text': '''X (Twitter) Terms of Service Summary:

1. Content License: You grant X a worldwide, non-exclusive, royalty-free license to use, copy, modify, and distribute your content.

2. Data Collection: We collect tweets, DMs, profile info, device data, and browsing history.

3. Advertising: Your data is used for targeted advertising across the platform.

4. Third-Party Apps: Apps you connect to may access significant portions of your data.

5. Content Moderation: We can remove content or suspend accounts at our discretion.

6. API Usage: Third parties can access public tweets through our API.

7. Analytics: We track detailed engagement metrics on all your activity.

8. Data Sales: We may sell or share aggregated user data.'''
            },
            {
                'name': 'Instagram',
                'category': 'social',
                'icon_url': 'https://upload.wikimedia.org/wikipedia/commons/a/a5/Instagram_icon.png',
                'terms_text': '''Instagram Terms of Service Summary:

1. Content Rights: You grant us a non-exclusive, royalty-free, transferable, sub-licensable, worldwide license to host, use, distribute, modify your content.

2. Data Collection: We collect photos, videos, messages, comments, and usage data.

3. Meta Integration: Your data is shared across Meta platforms (Facebook, WhatsApp).

4. Facial Recognition: We use facial recognition technology on your photos.

5. Shopping Data: Purchase behavior and payment info is collected.

6. Influencer Tracking: Business account analytics are extensively monitored.

7. Story Archives: Stories are archived even after 24-hour expiry.

8. Ad Targeting: Detailed behavioral profiling for advertisement targeting.'''
            },
            {
                'name': 'LinkedIn',
                'category': 'professional',
                'icon_url': 'https://upload.wikimedia.org/wikipedia/commons/c/ca/LinkedIn_logo_initials.png',
                'terms_text': '''LinkedIn Terms of Service Summary:

1. Professional Data: We collect resume info, job history, skills, and professional connections.

2. Recruiter Access: Your profile data is accessible to recruiters and employers.

3. Message Scanning: We analyze messages for ad targeting and feature improvement.

4. Third-Party Integrations: Connected apps can access extensive profile data.

5. Content Visibility: Posts may appear in search engines and external sites.

6. Microsoft Integration: Data is shared within Microsoft ecosystem.

7. Learning Data: Your course progress and interests are tracked.

8. Salary Insights: We collect and use salary information for insights.'''
            }
        ]

        created_companies = []
        for company_data in sample_companies:
            existing = [c for c in self.get_all_companies() if c.get('name') == company_data['name']]
            if not existing:
                company = self.create_company(
                    name=company_data['name'],
                    category=company_data['category'],
                    terms_text=company_data['terms_text'],
                    icon_url=company_data['icon_url']
                )
                created_companies.append(company)

        return created_companies
