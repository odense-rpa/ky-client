class KYSelectors:
    class Login:
        MUNICIPALITY_SELECT = 'select#SelectedAuthenticationUrl'
        OK_BUTTON = 'input[type="button"][value="OK"]'
        SUBMIT_BUTTON = 'input[type="submit"]'
        USERNAME = 'input[name="loginfmt"]'
        PASSWORD = 'input[name="passwd"]'

    class Main:
        LOGO = 'img#fagsystem-logo'
        TOP_SEARCH = 'input#topSearch'

    class Borgere:
        PERSON_OPLYSNINGER = 'table#person-oplysninger'
        SAGSOVERSIGT = 'table#sagsoversigt'
        UBEHANDLEDE_OPGAVER = 'table#ubehandlede-opgaver'
        LIVSSITUATION = 'table#person-overblik-livssituation'
