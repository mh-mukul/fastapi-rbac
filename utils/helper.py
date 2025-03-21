class ResponseHelper:
    def success_response(self, status_code, message, data=None):
        return ({
            "status": status_code,
            "message": message,
            "data": data
        })

    def error_response(self, status_code, message, data=None):
        return ({
            "status": status_code,
            "message": message,
            "data": data
        })

    