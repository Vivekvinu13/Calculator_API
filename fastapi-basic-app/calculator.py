from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.openapi.docs import get_swagger_ui_html
from pydantic import BaseModel

import ast
import math
import operator


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="Powerful Calculator API",
    description=(
        "A simple but powerful calculator built with FastAPI. "
        "Supports arithmetic operations, powers, percentages, "
        "square roots, constants, and safe mathematical expressions."
    ),
    version="1.0.0",
    docs_url=None,
    redoc_url=None,
)


# ============================================================
# CUSTOM SWAGGER UI
# Only changes the background colour.
# Everything else remains Swagger's default.
# ============================================================

@app.get(
    "/docs",
    include_in_schema=False
)
async def custom_swagger_ui():

    response = get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title="Powerful Calculator API - Swagger UI"
    )

    html = response.body.decode("utf-8")

    custom_css = """
    <style>
        html,
        body {
            background-color: #81cdc6 !important;
        }
    </style>
    """

    html = html.replace(
        "</head>",
        custom_css + "</head>"
    )

    return HTMLResponse(
        content=html
    )


# ============================================================
# REQUEST MODELS
# ============================================================

class CalculationRequest(BaseModel):
    a: float
    b: float | None = None


class ExpressionRequest(BaseModel):
    expression: str


# ============================================================
# SAFE EXPRESSION EVALUATOR
# ============================================================

OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
    ast.FloorDiv: operator.floordiv,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def safe_calculate(node):
    """
    Safely evaluate a mathematical AST.
    eval() is never used.
    """

    # --------------------------------------------------------
    # NUMBER
    # --------------------------------------------------------

    if isinstance(node, ast.Constant):

        if isinstance(
            node.value,
            (int, float)
        ):

            value = float(
                node.value
            )

            if not math.isfinite(value):

                raise ValueError(
                    "Number must be finite."
                )

            return value

        raise ValueError(
            "Only numbers are allowed."
        )


    # --------------------------------------------------------
    # UNARY OPERATION
    # --------------------------------------------------------

    if isinstance(
        node,
        ast.UnaryOp
    ):

        operation = OPERATORS.get(
            type(node.op)
        )

        if operation is None:

            raise ValueError(
                "Unsupported unary operator."
            )

        return operation(
            safe_calculate(
                node.operand
            )
        )


    # --------------------------------------------------------
    # BINARY OPERATION
    # --------------------------------------------------------

    if isinstance(
        node,
        ast.BinOp
    ):

        operation = OPERATORS.get(
            type(node.op)
        )

        if operation is None:

            raise ValueError(
                "Unsupported operator."
            )

        left = safe_calculate(
            node.left
        )

        right = safe_calculate(
            node.right
        )

        # Division/modulo by zero
        if isinstance(
            node.op,
            (
                ast.Div,
                ast.FloorDiv,
                ast.Mod
            )
        ):

            if right == 0:

                raise ValueError(
                    "Division by zero is not allowed."
                )

        # Limit exponent size
        if isinstance(
            node.op,
            ast.Pow
        ):

            if abs(right) > 100:

                raise ValueError(
                    "Exponent is too large."
                )

        try:

            result = operation(
                left,
                right
            )

        except OverflowError:

            raise ValueError(
                "Result is too large."
            )

        except ZeroDivisionError:

            raise ValueError(
                "Division by zero is not allowed."
            )

        if not math.isfinite(
            float(result)
        ):

            raise ValueError(
                "Result is not finite."
            )

        return result


    # --------------------------------------------------------
    # UNSUPPORTED
    # --------------------------------------------------------

    raise ValueError(
        "Unsupported expression."
    )


# ============================================================
# EVALUATE EXPRESSION
# ============================================================

def evaluate_expression(
    expression: str
):

    expression = (
        expression
        .replace("^", "**")
        .strip()
    )

    if not expression:

        raise ValueError(
            "Expression cannot be empty."
        )

    try:

        tree = ast.parse(
            expression,
            mode="eval"
        )

    except SyntaxError:

        raise ValueError(
            "Invalid mathematical expression."
        )

    return safe_calculate(
        tree.body
    )


# ============================================================
# HOME
# ============================================================

@app.get("/")
def home():

    return {
        "message": "Welcome to Powerful Calculator API",
        "documentation": "/docs",
        "version": "1.0.0"
    }


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
def health():

    return {
        "status": "healthy"
    }


# ============================================================
# ADD
# ============================================================

@app.get("/add")
def add(
    a: float,
    b: float
):

    return {
        "operation": "addition",
        "a": a,
        "b": b,
        "result": a + b
    }


# ============================================================
# SUBTRACT
# ============================================================

@app.get("/subtract")
def subtract(
    a: float,
    b: float
):

    return {
        "operation": "subtraction",
        "a": a,
        "b": b,
        "result": a - b
    }


# ============================================================
# MULTIPLY
# ============================================================

@app.get("/multiply")
def multiply(
    a: float,
    b: float
):

    return {
        "operation": "multiplication",
        "a": a,
        "b": b,
        "result": a * b
    }


# ============================================================
# DIVIDE
# ============================================================

@app.get("/divide")
def divide(
    a: float,
    b: float
):

    if b == 0:

        raise HTTPException(
            status_code=400,
            detail="Cannot divide by zero."
        )

    return {
        "operation": "division",
        "a": a,
        "b": b,
        "result": a / b
    }


# ============================================================
# POWER
# ============================================================

@app.get("/power")
def power(
    a: float,
    b: float
):

    if abs(b) > 100:

        raise HTTPException(
            status_code=400,
            detail="Exponent is too large."
        )

    try:

        result = a ** b

    except OverflowError:

        raise HTTPException(
            status_code=400,
            detail="Result is too large."
        )

    return {
        "operation": "power",
        "base": a,
        "exponent": b,
        "result": result
    }


# ============================================================
# MODULO
# ============================================================

@app.get("/modulo")
def modulo(
    a: float,
    b: float
):

    if b == 0:

        raise HTTPException(
            status_code=400,
            detail="Cannot use zero as divisor."
        )

    return {
        "operation": "modulo",
        "a": a,
        "b": b,
        "result": a % b
    }


# ============================================================
# PERCENTAGE
# ============================================================

@app.get("/percentage")
def percentage(
    a: float,
    b: float
):

    return {
        "operation": "percentage",
        "number": a,
        "percentage": b,
        "result": a * b / 100
    }


# ============================================================
# SQUARE ROOT
# ============================================================

@app.get("/sqrt")
def square_root(
    number: float
):

    if number < 0:

        raise HTTPException(
            status_code=400,
            detail=(
                "Square root of a negative "
                "number is not supported."
            )
        )

    return {
        "operation": "square root",
        "number": number,
        "result": math.sqrt(number)
    }


# ============================================================
# ADVANCED EXPRESSION CALCULATOR
# ============================================================

@app.post("/calculate")
def calculate(
    data: ExpressionRequest
):

    try:

        result = evaluate_expression(
            data.expression
        )

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    return {
        "expression": data.expression,
        "result": result
    }


# ============================================================
# MATHEMATICAL CONSTANTS
# ============================================================

@app.get("/constants")
def constants():

    return {
        "pi": math.pi,
        "e": math.e,
        "tau": math.tau
    }