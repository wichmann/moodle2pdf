
WINDOWS = False
LINUX = False
ELSE = True

if LINUX:
    import notify2
    notify2.init('MoodleEditor')
    n = notify2.Notification('Summary', 'Some body text',
                             'notification-message-im')
    n.show()
elif WINDOWS:
    from win10toast import ToastNotifier
    toaster = ToastNotifier()
    toaster.show_toast('Sample Notification', 'New packages found!')
elif ELSE:
    from plyer import notification
    notification.notify(
        title='Here is the title',
        message='Here is the message',
        app_icon='',  # e.g. 'C:\\icon_32x32.ico'
        timeout=10,  # seconds
    )
