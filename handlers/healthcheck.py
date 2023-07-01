# Fake Health Check
def fake_health_check():
    """
    Used to let Digital Ocean know the application is alive.
    Since the bot needs to start in order to boot up a port, this is used temporarily
    """
    import socket
    import sys

    HOST = ''
    PORT = 8005

    fake_health_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        fake_health_socket.bind((HOST, PORT))

    except socket.error as msg:
        print('Bind failed. Error Code : ' + str(msg[0]) + ' Message ' + msg[1])
        sys.exit()

    print('Socket bind complete')

    # Listen and accept incoming call. We expect this to be the digitalocean health check
    fake_health_socket.listen(10)
    conn, addr = fake_health_socket.accept()

    print('Successfully lied to ' + addr[0] + ':' + str(addr[1]) + "That our health check is 'valid'")

    # Now we close the port so our voting webhook can use it
    fake_health_socket.close()
