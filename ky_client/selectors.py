def _nav(key: str) -> str:
    return f'[data-textkey="fagsystem.person.navigation.{key}"]'


class KYSelectors:
    class Login:
        MUNICIPALITY_SELECT = "select#SelectedAuthenticationUrl"
        OK_BUTTON = 'input[type="button"][value="OK"]'
        SUBMIT_BUTTON = 'input[type="submit"]'
        USERNAME = 'input[name="loginfmt"]'
        PASSWORD = 'input[name="passwd"]'

    class Main:
        LOGO = "img#fagsystem-logo"
        TOP_SEARCH = "input#topSearch"
        OVERBLIK = _nav("person_overblik")
        JOURNALNOTATER_DOKUMENTER = _nav("person_journalnotater_dokumenter")
        HAENDELSER = _nav("person_haendelser")
        UDBETALING = _nav("person_udbetalinger")
        KONTERINGER = _nav("person_konteringer")
        INDTAEGTER = _nav("person_indtaegter")
        SANKTIONER = _nav("person_sanktioner")
        FERIE = _nav("person_ferie")
        FORDRINGER = _nav("person_fordringer")
        MODREGNINGER = _nav("person_modregningsanmodninger")
        FUB = _nav("person_fub")
        SKAT = _nav("skatteindberetninger")
        JOBCENTER = _nav("person_jobcenter")
        MEDICINTILSKUD = _nav("person_medicintilskud")

    class Borgere:
        # Overblik
        PERSON_OPLYSNINGER = "table#person-oplysninger"
        SAGSOVERSIGT = "table#sagsoversigt"
        UBEHANDLEDE_OPGAVER = "table#ubehandlede-opgaver"
        LIVSSITUATION = "table#person-overblik-livssituation"

        # Udbetaling
        @staticmethod
        def KOMMENDE_UDBETALINGER(p_id: str) -> str:
            return f"table#tabel_kommende_udbetalinger_{p_id}"
