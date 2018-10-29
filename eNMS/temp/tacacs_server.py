else:
    try:
        tacacs_server = db.session.query(TacacsServer).one()
        tacacs_client = TACACSClient(
            str(tacacs_server.ip_address),
            int(tacacs_server.port),
            str(tacacs_server.password)
        )
        if tacacs_client.authenticate(
            name,
            user_password,
            TAC_PLUS_AUTHEN_TYPE_ASCII
        ).valid:
            user = User(name=name, password=user_password)
            db.session.add(user)
            db.session.commit()
            login_user(user)
            return redirect(url_for('base_blueprint.dashboard'))
    except NoResultFound:
        pass
return render_template('errors/page_403.html')