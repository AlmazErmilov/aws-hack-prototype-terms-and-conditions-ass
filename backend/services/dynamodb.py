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
                       terms_risks: List[Dict] = None, summary: str = None,
                       icon_url: str = None, cookie_text: str = None,
                       cookie_summary: str = None, cookie_risks: List[Dict] = None) -> Dict[str, Any]:
        """Create a new company entry"""
        company_id = str(uuid.uuid4())

        item = {
            'id': company_id,
            'name': name,
            'category': category,
            'terms_text': terms_text,
            'terms_risks': terms_risks or [],
            'summary': summary or '',
            'icon_url': icon_url or '',
            'last_updated': datetime.utcnow().isoformat(),
            # Cookie policy fields
            'cookie_text': cookie_text or '',
            'cookie_summary': cookie_summary or '',
            'cookie_risks': cookie_risks or []
        }

        self.table.put_item(Item=item)
        return item

    def update_company_analysis(self, company_id: str, terms_risks: List[Dict], summary: str) -> bool:
        """Update company with T&C analysis results"""
        try:
            self.table.update_item(
                Key={'id': company_id},
                UpdateExpression='SET terms_risks = :r, summary = :s, last_updated = :u',
                ExpressionAttributeValues={
                    ':r': terms_risks,
                    ':s': summary,
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

    def delete_company(self, company_id: str) -> bool:
        """Delete a company"""
        try:
            self.table.delete_item(Key={'id': company_id})
            return True
        except Exception:
            return False

    def migrate_risks_to_terms_risks(self) -> Dict[str, Any]:
        """
        Migration: Rename 'risks' field to 'terms_risks' for all existing companies.
        This copies data from 'risks' to 'terms_risks' and removes the old field.
        Safe to run multiple times - skips already migrated records.
        """
        companies = self.get_all_companies()
        migrated = 0
        skipped = 0
        errors = []

        for company in companies:
            company_id = company.get('id')
            has_old_risks = 'risks' in company
            has_new_terms_risks = 'terms_risks' in company

            # Skip if already migrated (has terms_risks, no risks)
            if has_new_terms_risks and not has_old_risks:
                skipped += 1
                continue

            # Skip if nothing to migrate
            if not has_old_risks and not has_new_terms_risks:
                skipped += 1
                continue

            try:
                # Get the risks data (prefer old field for migration)
                risks_data = company.get('risks', company.get('terms_risks', []))

                # Update: set terms_risks and remove old risks field
                self.table.update_item(
                    Key={'id': company_id},
                    UpdateExpression='SET terms_risks = :tr, last_updated = :u REMOVE risks',
                    ExpressionAttributeValues={
                        ':tr': risks_data,
                        ':u': datetime.utcnow().isoformat()
                    }
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
