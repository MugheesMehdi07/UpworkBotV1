import firebase_admin
from firebase_admin import credentials, messaging

cred = credentials.Certificate("firebase-admin-sdk-creds.json")
firebase_admin.initialize_app(cred)


def notification(instance):
    try:
        print('in notification func', instance)
        topic = 'upworkjobs'

        # Define the web push notification action
        action = messaging.WebpushNotificationAction(
            title='View Job',
            action='openJob',
        )

        message = messaging.Message(
            notification=messaging.Notification(
                title='UpworkBot',
                body=instance.job_title,
            ),
            data={
                'click_action': f'http://localhost:3000/jobs/{instance.id}',
                'job_link': f'http://localhost:3000/jobs/{instance.id}',
            },
            webpush=messaging.WebpushConfig(
                notification=messaging.WebpushNotification(
                    actions=[action],  # Include the action in the list of actions
                ),
            ),
            topic=topic,
        )

        # Send the notification to the specified topic
        response = messaging.send(message)
        print('response', response)
    except Exception as e:
        print('error', str(e))

