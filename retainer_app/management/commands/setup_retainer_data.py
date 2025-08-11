from django.core.management.base import BaseCommand
from django.db import transaction
from retainer_app.models import LawFirm, DocumentTemplate, EmailTemplate


class Command(BaseCommand):
    help = 'Set up initial retainer data for Bullock Legal Group - Kratom cases'

    def handle(self, *args, **options):
        with transaction.atomic():
            self.stdout.write(self.style.SUCCESS('Setting up Retainer Data for Bullock Legal Group...'))
            
            # Get or create Bullock Legal Group
            bullock_firm, created = LawFirm.objects.get_or_create(
                name='Bullock Legal Group',
                defaults={
                    'subdomain': 'bullock',
                    'contact_email': 'admin@bullocklegal.com',
                    'phone_number': '555-0123',
                    'address': '123 Legal Street, Law City, LC 12345',
                    'is_active': True
                }
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f'✓ Created law firm: {bullock_firm.name}'))
            else:
                self.stdout.write(f'✓ Found existing law firm: {bullock_firm.name}')

            # Create Kratom Retainer Document Template
            kratom_template, created = DocumentTemplate.objects.get_or_create(
                name='Kratom Retainer',
                law_firm=bullock_firm,
                defaults={
                    'display_name': 'Kratom Retainer Agreement',
                    'nextkeysign_template_id': '26',  # Based on your webhook data
                    'description': '''
Retainer agreement for Kratom-related injury cases including:
- Overdose cases
- Addiction cases  
- Organ damage cases
- Heart attack cases
- Wrongful death cases

Covers all major Kratom brands including OPMS, Whole Herbs, MIT 45, 
7-hydroxymitragynine (7-OH) products, and other retail/gas station Kratom products.
                    '''.strip(),
                    'is_active': True
                }
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f'✓ Created document template: {kratom_template.display_name}'))
            else:
                self.stdout.write(f'✓ Found existing document template: {kratom_template.display_name}')

            # Create Kratom Retainer Email Template
            kratom_email_template, created = EmailTemplate.objects.get_or_create(
                name='Kratom Invitation',
                law_firm=bullock_firm,
                defaults={
                    'template_type': 'invitation',
                    'subject': 'Kratom Case - Retainer Agreement Required for [Name]',
                    'body': '''<!doctype html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <style>
        /* Fallback mobile styles (some clients will use these) */
        @media only screen and (max-width:480px) {
            .container {
                width: 100% !important;
                padding: 10px !important;
            }
            .hero-img {
                width: 100% !important;
                height: auto !important;
            }
            .two-col {
                display: block !important;
                width: 100% !important;
            }
            .button {
                display: block !important;
                width: 100% !important;
                box-sizing: border-box;
            }
            .small {
                font-size: 14px !important;
            }
        }
    </style>
</head>
<body style="margin:0;padding:0;background-color:#f4f4f5;font-family:Arial, Helvetica, sans-serif;-webkit-text-size-adjust:100%;-ms-text-size-adjust:100%;">
    <!--[if mso]>
  <style>
    .fallback-font { font-family: Arial, Helvetica, sans-serif !important; }
  </style>
  <![endif]-->

    <table role="presentation" width="100%" border="0" cellspacing="0" cellpadding="0" align="center" style="background-color:#f4f4f5;">
        <tr>
            <td align="center" style="padding:20px 10px;">
                <!-- Container -->
                <table role="presentation" class="container" width="600" border="0" cellspacing="0" cellpadding="0" style="width:600px;max-width:600px;background-color:#ffffff;border-radius:8px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.05);">
                    <!-- Header image -->
                    <tr>
                        <td style="padding:0;">
                            <img class="hero-img" src="data:image/svg+xml;utf8,
                <svg xmlns='http://www.w3.org/2000/svg' width='1200' height='300'>
                  <defs>
                    <linearGradient id='g' x1='0' x2='1' y1='0' y2='1'>
                      <stop offset='0' stop-color='%233462A8'/>
                      <stop offset='1' stop-color='%230C7A5E'/>
                    </linearGradient>
                  </defs>
                  <rect width='100%' height='100%' fill='url(%23g)'/>
                  <text x='50%' y='48%' font-family='Arial, Helvetica, sans-serif' font-size='46' fill='%23ffffff' text-anchor='middle' font-weight='700'>Kratom Legal Help</text>
                  <text x='50%' y='70%' font-family='Arial, Helvetica, sans-serif' font-size='18' fill='%23ffffff' text-anchor='middle'>Bullock Legal Group — Case evaluations available</text>
                </svg>" alt="Kratom Legal Help - Bullock Legal Group" width="600" style="display:block;width:100%;height:auto;border:0;line-height:100%;outline:none;text-decoration:none;">
                        </td>
                    </tr>

                    <!-- Body -->
                    <tr>
                        <td style="padding:20px 28px 12px 28px;color:#111827;">
                            <h1 class="fallback-font" style="margin:0 0 12px 0;font-size:20px;line-height:26px;color:#111827;font-weight:700;">
                                IF YOU OR A LOVED ONE USED KRATOM YOU MAY BE ELIGIBLE FOR COMPENSATION</h1>

                            <p style="margin:0 0 12px 0;font-size:14px;line-height:20px;color:#444;">
                                Dear [Name],
                            </p>

                            <p style="margin:0 0 12px 0;font-size:14px;line-height:20px;color:#444;">
                                Bullock Legal Group is pursuing claims on behalf of our clients who have sustained severe injuries such as overdose, addiction, organ damage, heart attacks and death due to kratom use. kratom is a plant native to Southeast Asia that is marketed online and sold in gas stations and retail shops as a herbal supplement. kratom has been traditionally used for its stimulant and sedative effects, not unlike opioids.
                            </p>

                            <p style="margin:0 0 14px 0;font-size:14px;line-height:20px;color:#444;">
                                People report using kratom products to alleviate drug withdrawal symptoms (particularly for opioids), to alleviate pain, and to help manage anxiety and depression. People who use kratom report both stimulant-like effects (increased energy, alertness, and rapid heart rate) and effects that are similar to opioids and sedatives (relaxation, pain relief, and confusion).
                            </p>

                            <p style="margin:0 0 14px 0;font-size:14px;line-height:20px;color:#444;">
                                In the U.S., it is available in various forms, such as powders, capsules, and teas. Despite its widespread availability, kratom is not approved by the Food and Drug Administration (FDA) and lacks standardized dosing guidelines, leading to potential misuse and health risks.
                            </p>

                            <h2 style="margin:10px 0 8px 0;font-size:18px;color:#111827;">Case Evaluation</h2>
                            <p style="margin:0 0 10px 0;font-size:14px;line-height:20px;color:#444;">
                                For a no obligation and no pressure attorney case review involving a severe injury or death related to kratom, we need the following documents:
                            </p>

                            <!-- Two-column lists (will stack on mobile) -->
                            <table role="presentation" width="100%" border="0" cellspacing="0" cellpadding="0">
                                <tr>
                                    <td class="two-col" valign="top" style="padding-right:10px;width:50%;font-size:14px;color:#444;">
                                        <strong style="display:block;margin-bottom:6px;">For Kratom Wrongful Death Evaluation</strong>
                                        <ul style="margin:0 0 12px 18px;padding:0;color:#444;">
                                            <li>Brand of kratom product used</li>
                                            <li>Autopsy report</li>
                                            <li>Toxicology report</li>
                                            <li>Death certificate</li>
                                        </ul>
                                    </td>
                                    <td class="two-col" valign="top" style="width:50%;font-size:14px;color:#444;">
                                        <strong style="display:block;margin-bottom:6px;">For Kratom Severe Injury Evaluation</strong>
                                        <ul style="margin:0 0 12px 18px;padding:0;color:#444;">
                                            <li>Brand of kratom product used</li>
                                            <li>Photos of the product labeling</li>
                                            <li>Where it was purchased</li>
                                            <li>Reasons for using</li>
                                            <li>Hospital Records-Organ Damage, Overdose, Heart Attack, Overdose</li>
                                        </ul>
                                    </td>
                                </tr>
                            </table>

                            <h3 style="margin:6px 0 6px 0;font-size:14px;color:#111827;">Kratom Brands</h3>
                            <table role="presentation" width="100%" border="0" cellspacing="0" cellpadding="0">
                                <tr>
                                    <td class="two-col" valign="top" style="padding-right:10px;width:50%;font-size:14px;color:#444;">
                                        <ul style="margin:0 0 12px 18px;padding:0;color:#444;">
                                            <li>OPMS</li>
                                            <li>MIT 45</li>
                                            <li>7Ohmz</li>
                                            <li>Dr. Kratom</li>
                                            <li>Earth Kratom</li>
                                            <li>Golden Monk</li>
                                            <li>Kats Botanicals</li>
                                            <li>KrakenKrave Botanicals</li>
                                            <li>NuWave Botanicals</li>
                                        </ul>
                                    </td>
                                    <td class="two-col" valign="top" style="width:50%;font-size:14px;color:#444;">
                                        <ul style="margin:0 0 12px 18px;padding:0;color:#444;">
                                            <li>Whole Herbs, Remarkable Herbs</li>
                                            <li>Hush Kratom</li>
                                            <li>KRATOMade</li>
                                            <li>Chief Kratom</li>
                                            <li>EXP Botanicals</li>
                                            <li>Happy Hippo</li>
                                            <li>King Kratom</li>
                                            <li>Mitragaia</li>
                                        </ul>
                                    </td>
                                </tr>
                            </table>

                            <h3 style="margin:8px 0 6px 0;font-size:14px;color:#111827;">7-hydroxymitragynine (7-OH) Brands</h3>
                            <table role="presentation" width="100%" border="0" cellspacing="0" cellpadding="0">
                                <tr>
                                    <td class="two-col" valign="top" style="padding-right:10px;width:50%;font-size:14px;color:#444;">
                                        <ul style="margin:0 0 12px 18px;padding:0;color:#444;">
                                            <li>7OHMZ</li>
                                            <li>CBD American Shaman</li>
                                            <li>Jubi</li>
                                            <li>7 O'Heaven</li>
                                            <li>On7</li>
                                            <li>Eat OHMZ</li>
                                            <li>Roxy Complex</li>
                                            <li>Zohm</li>
                                        </ul>
                                    </td>
                                    <td class="two-col" valign="top" style="width:50%;font-size:14px;color:#444;">
                                        <ul style="margin:0 0 12px 18px;padding:0;color:#444;">
                                            <li>7Tabz</li>
                                            <li>Press'D</li>
                                            <li>Ultra Seven</li>
                                            <li>Pure Ohms</li>
                                            <li>Opia</li>
                                            <li>Hyku</li>
                                            <li>7rx</li>
                                        </ul>
                                    </td>
                                </tr>
                            </table>

                            <p style="margin:14px 0 16px 0;font-size:14px;line-height:20px;color:#444;">
                                <strong>Case Details:</strong><br>
                                Client: [Name]<br>
                                Injured Party: [First Name Injured] [Last Name Injured]<br>
                                State: [State]<br>
                                Case ID: [External ID]
                            </p>

                            <!-- CTA button -->
                            <table role="presentation" width="100%" border="0" cellspacing="0" cellpadding="0" style="margin:6px 0 16px 0;">
                                <tr>
                                    <td align="center">
                                        <p style="margin:0 0 12px 0;font-size:14px;line-height:20px;color:#444;">
                                            Please review and sign the attached retainer agreement to proceed with your case evaluation.
                                        </p>
                                        <a href="{submitter.link}" class="button" style="background-color:#f46c46;color:#ffffff;text-decoration:none;padding:12px 18px;border-radius:6px;display:inline-block;font-weight:600;font-size:16px;">
                                            Sign Retainer Agreement
                                        </a>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>

                    <!-- Footer -->
                    <tr>
                        <td style="padding:12px 28px 20px 28px;background-color:#fafafa;border-top:1px solid #eee;">
                            <table role="presentation" width="100%" border="0" cellspacing="0" cellpadding="0">
                                <tr>
                                    <td style="font-size:13px;color:#6b7280;">
                                        Bullock Legal Group<br>
                                        Kratom Litigation Department
                                    </td>
                                    <td align="right" style="font-size:13px;color:#6b7280;">
                                        <a href="mailto:info@bullocklegalgroup.com" style="color:#0c7a5e;text-decoration:none;">info@bullocklegalgroup.com</a> 
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>'''.strip(),
                    'is_active': True
                }
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f'✓ Created email template: {kratom_email_template.name}'))
            else:
                self.stdout.write(f'✓ Found existing email template: {kratom_email_template.name}')

            self.stdout.write(self.style.SUCCESS('\n🎉 Retainer system setup completed successfully!'))
            self.stdout.write(self.style.SUCCESS('\nSetup Summary:'))
            self.stdout.write(f'  • Law Firm: {bullock_firm.name}')
            self.stdout.write(f'  • Document Template: {kratom_template.display_name}')
            self.stdout.write(f'  • Email Templates: {EmailTemplate.objects.filter(law_firm=bullock_firm).count()} created')
            self.stdout.write(self.style.SUCCESS('\nYou can now:'))
            self.stdout.write('  1. Upload Excel files with Kratom case leads')
            self.stdout.write('  2. Process retainer agreements automatically')
            self.stdout.write('  3. Track document signing progress')
            self.stdout.write('  4. Create additional retainer types in the future (Realpage, etc.)')
