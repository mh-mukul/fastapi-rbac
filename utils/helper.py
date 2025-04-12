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

    def paginate_query(self, query, page: int, limit: int):
        total = query.count()
        items = query.offset((page - 1) * limit).limit(limit).all()
        return items, total
