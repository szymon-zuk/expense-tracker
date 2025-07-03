from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.models.expenses import Category, Expense, User
from backend.app.schemas.expenses import CurrencyEnum


class TestGetAllExpenses:
    """Test cases for GET /expenses endpoint."""

    def test_get_all_expenses_success(
        self, client: TestClient, test_expenses: list[Expense]
    ):
        """Test successful retrieval of all expenses."""
        response = client.get("/expenses")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        assert data[0]["name"] == "Grocery Shopping"
        assert data[1]["name"] == "Gas Station"
        assert data[2]["name"] == "Movie Tickets"

    def test_get_expenses_with_category_filter(
        self, client: TestClient, test_expenses: list[Expense]
    ):
        """Test filtering expenses by category."""
        response = client.get("/expenses?category_id=1")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Grocery Shopping"
        assert data[0]["category_id"] == 1

    def test_get_expenses_with_pagination(
        self, client: TestClient, test_expenses: list[Expense]
    ):
        """Test pagination of expenses."""
        response = client.get("/expenses?skip=1&limit=2")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["name"] == "Gas Station"
        assert data[1]["name"] == "Movie Tickets"

    def test_get_expenses_with_invalid_category_filter(
        self, client: TestClient, test_expenses: list[Expense]
    ):
        """Test filtering with non-existent category."""
        response = client.get("/expenses?category_id=999")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0

    def test_get_expenses_empty_result(self, client: TestClient):
        """Test getting expenses when no expenses exist."""
        response = client.get("/expenses")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0

    def test_get_expenses_user_isolation(
        self, client_user_2: TestClient, test_expenses: list[Expense]
    ):
        """Test that users only see their own expenses."""
        response = client_user_2.get("/expenses")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0  # User 2 has no expenses


class TestGetExpenseStatistics:
    """Test cases for GET /expenses/statistics endpoint."""

    def test_get_statistics_all_time(
        self, client: TestClient, test_expenses: list[Expense]
    ):
        """Test getting statistics for all time."""
        response = client.get("/expenses/statistics")

        assert response.status_code == 200
        data = response.json()
        assert data["total_amount"] == 105.0  # 50 + 30 + 25
        assert data["total_expenses"] == 3
        assert data["average_expense"] == 35.0
        assert data["period_summary"]["period_type"] == "All time"
        assert len(data["currency_breakdown"]) == 2  # USD and EUR
        assert len(data["category_breakdown"]) == 3

    def test_get_statistics_with_date_range(
        self, client: TestClient, test_expenses: list[Expense]
    ):
        """Test getting statistics with date range."""
        response = client.get(
            "/expenses/statistics?start_date=2023-01-01&end_date=2023-01-31"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_amount"] == 80.0  # Only January expenses
        assert data["total_expenses"] == 2
        assert data["average_expense"] == 40.0
        assert "Custom" in data["period_summary"]["period_type"]

    def test_get_statistics_with_category_filter(
        self, client: TestClient, test_expenses: list[Expense]
    ):
        """Test getting statistics filtered by category."""
        response = client.get("/expenses/statistics?category_id=1")

        assert response.status_code == 200
        data = response.json()
        assert data["total_amount"] == 50.0
        assert data["total_expenses"] == 1
        assert data["average_expense"] == 50.0
        assert len(data["category_breakdown"]) == 1

    def test_get_statistics_currency_breakdown(
        self, client: TestClient, test_expenses: list[Expense]
    ):
        """Test currency breakdown in statistics."""
        response = client.get("/expenses/statistics")

        assert response.status_code == 200
        data = response.json()
        currency_breakdown = data["currency_breakdown"]

        usd_stats = next(
            (c for c in currency_breakdown if c["currency"] == "USD"), None
        )
        eur_stats = next(
            (c for c in currency_breakdown if c["currency"] == "EUR"), None
        )

        assert usd_stats is not None
        assert usd_stats["total_amount"] == 80.0
        assert usd_stats["expense_count"] == 2

        assert eur_stats is not None
        assert eur_stats["total_amount"] == 25.0
        assert eur_stats["expense_count"] == 1

    def test_get_statistics_empty_result(self, client: TestClient):
        """Test getting statistics when no expenses exist."""
        response = client.get("/expenses/statistics")

        assert response.status_code == 200
        data = response.json()
        assert data["total_amount"] == 0.0
        assert data["total_expenses"] == 0
        assert data["average_expense"] == 0.0
        assert len(data["currency_breakdown"]) == 0
        assert len(data["category_breakdown"]) == 0

    def test_get_statistics_user_isolation(
        self, client_user_2: TestClient, test_expenses: list[Expense]
    ):
        """Test that statistics are isolated by user."""
        response = client_user_2.get("/expenses/statistics")

        assert response.status_code == 200
        data = response.json()
        assert data["total_amount"] == 0.0
        assert data["total_expenses"] == 0


class TestGetExpenseById:
    """Test cases for GET /expenses/{expense_id} endpoint."""

    def test_get_expense_by_id_success(
        self, client: TestClient, test_expenses: list[Expense]
    ):
        """Test successful retrieval of expense by ID."""
        response = client.get("/expenses/1")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1
        assert data["name"] == "Grocery Shopping"
        assert data["amount"] == 50.0
        assert data["currency"] == "USD"

    def test_get_expense_by_id_not_found(self, client: TestClient):
        """Test getting non-existent expense."""
        response = client.get("/expenses/999")

        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"]

    def test_get_expense_by_id_forbidden(
        self, client_user_2: TestClient, test_expenses: list[Expense]
    ):
        """Test accessing expense owned by another user."""
        response = client_user_2.get("/expenses/1")

        assert response.status_code == 403
        data = response.json()
        assert "only access your own expenses" in data["detail"]


class TestCreateExpense:
    """Test cases for POST /expenses endpoint."""

    def test_create_expense_success(
        self, client: TestClient, test_categories: list[Category]
    ):
        """Test successful expense creation."""
        expense_data = {
            "name": "Coffee",
            "description": "Morning coffee",
            "amount": 5.0,
            "currency": "USD",
            "category_id": 1,
        }

        response = client.post("/expenses", json=expense_data)

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Coffee"
        assert data["amount"] == 5.0
        assert data["currency"] == "USD"
        assert data["category_id"] == 1
        assert data["owner_id"] == 1
        assert "id" in data

    def test_create_expense_invalid_category(self, client: TestClient):
        """Test creating expense with invalid category."""
        expense_data = {
            "name": "Coffee",
            "description": "Morning coffee",
            "amount": 5.0,
            "currency": "USD",
            "category_id": 999,
        }

        response = client.post("/expenses", json=expense_data)

        assert response.status_code == 400
        data = response.json()
        assert "Category with id 999 not found" in data["detail"]

    def test_create_expense_missing_required_fields(self, client: TestClient):
        """Test creating expense with missing required fields."""
        expense_data = {"description": "Missing name and amount"}

        response = client.post("/expenses", json=expense_data)

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_create_expense_invalid_currency(
        self, client: TestClient, test_categories: list[Category]
    ):
        """Test creating expense with invalid currency."""
        expense_data = {
            "name": "Coffee",
            "description": "Morning coffee",
            "amount": 5.0,
            "currency": "INVALID",
            "category_id": 1,
        }

        response = client.post("/expenses", json=expense_data)

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_create_expense_negative_amount(
        self, client: TestClient, test_categories: list[Category]
    ):
        """Test creating expense with negative amount."""
        expense_data = {
            "name": "Refund",
            "description": "Money back",
            "amount": -10.0,
            "currency": "USD",
            "category_id": 1,
        }

        response = client.post("/expenses", json=expense_data)

        assert response.status_code == 201
        data = response.json()
        assert data["amount"] == -10.0  # Negative amounts should be allowed for refunds


class TestUpdateExpense:
    """Test cases for PUT /expenses/{expense_id} endpoint."""

    def test_update_expense_success(
        self, client: TestClient, test_expenses: list[Expense]
    ):
        """Test successful expense update."""
        update_data = {
            "name": "Updated Grocery Shopping",
            "amount": 75.0,
            "description": "Updated description",
        }

        response = client.put("/expenses/1", json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Grocery Shopping"
        assert data["amount"] == 75.0
        assert data["description"] == "Updated description"
        assert data["currency"] == "USD"  # Unchanged fields remain

    def test_update_expense_partial_update(
        self, client: TestClient, test_expenses: list[Expense]
    ):
        """Test partial expense update."""
        update_data = {"amount": 60.0}

        response = client.put("/expenses/1", json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert data["amount"] == 60.0
        assert data["name"] == "Grocery Shopping"  # Other fields unchanged

    def test_update_expense_not_found(self, client: TestClient):
        """Test updating non-existent expense."""
        update_data = {"name": "Updated name"}

        response = client.put("/expenses/999", json=update_data)

        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"]

    def test_update_expense_forbidden(
        self, client_user_2: TestClient, test_expenses: list[Expense]
    ):
        """Test updating expense owned by another user."""
        update_data = {"name": "Hacked expense"}

        response = client_user_2.put("/expenses/1", json=update_data)

        assert response.status_code == 403
        data = response.json()
        assert "only update your own expenses" in data["detail"]

    def test_update_expense_invalid_currency(
        self, client: TestClient, test_expenses: list[Expense]
    ):
        """Test updating expense with invalid currency."""
        update_data = {"currency": "INVALID"}

        response = client.put("/expenses/1", json=update_data)

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data


class TestDeleteExpense:
    """Test cases for DELETE /expenses/{expense_id} endpoint."""

    def test_delete_expense_success(
        self, client: TestClient, test_expenses: list[Expense]
    ):
        """Test successful expense deletion."""
        response = client.delete("/expenses/1")

        assert response.status_code == 204

        # Verify expense is deleted
        get_response = client.get("/expenses/1")
        assert get_response.status_code == 404

    def test_delete_expense_not_found(self, client: TestClient):
        """Test deleting non-existent expense."""
        response = client.delete("/expenses/999")

        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"]

    def test_delete_expense_forbidden(
        self, client_user_2: TestClient, test_expenses: list[Expense]
    ):
        """Test deleting expense owned by another user."""
        response = client_user_2.delete("/expenses/1")

        assert response.status_code == 403
        data = response.json()
        assert "only delete your own expenses" in data["detail"]

    def test_delete_expense_verify_isolation(
        self, client: TestClient, test_expenses: list[Expense]
    ):
        """Test that deleting an expense doesn't affect other expenses."""
        # Delete one expense
        response = client.delete("/expenses/1")
        assert response.status_code == 204

        # Verify other expenses still exist
        get_response = client.get("/expenses")
        assert get_response.status_code == 200
        data = get_response.json()
        assert len(data) == 2
        assert all(expense["id"] != 1 for expense in data)


class TestExpenseEndpointsIntegration:
    """Integration tests for expense endpoints."""

    def test_create_update_delete_flow(
        self, client: TestClient, test_categories: list[Category]
    ):
        """Test complete CRUD flow for expenses."""
        # Create expense
        expense_data = {
            "name": "Test Expense",
            "description": "Test description",
            "amount": 100.0,
            "currency": "USD",
            "category_id": 1,
        }

        create_response = client.post("/expenses", json=expense_data)
        assert create_response.status_code == 201
        created_expense = create_response.json()
        expense_id = created_expense["id"]

        # Update expense
        update_data = {"name": "Updated Test Expense", "amount": 150.0}

        update_response = client.put(f"/expenses/{expense_id}", json=update_data)
        assert update_response.status_code == 200
        updated_expense = update_response.json()
        assert updated_expense["name"] == "Updated Test Expense"
        assert updated_expense["amount"] == 150.0

        # Get expense
        get_response = client.get(f"/expenses/{expense_id}")
        assert get_response.status_code == 200
        retrieved_expense = get_response.json()
        assert retrieved_expense["name"] == "Updated Test Expense"

        # Delete expense
        delete_response = client.delete(f"/expenses/{expense_id}")
        assert delete_response.status_code == 204

        # Verify deletion
        get_response = client.get(f"/expenses/{expense_id}")
        assert get_response.status_code == 404

    def test_expense_statistics_after_crud_operations(
        self, client: TestClient, test_categories: list[Category]
    ):
        """Test that statistics are correctly updated after CRUD operations."""
        # Initial state - no expenses
        stats_response = client.get("/expenses/statistics")
        assert stats_response.status_code == 200
        initial_stats = stats_response.json()
        assert initial_stats["total_expenses"] == 0

        # Create expense
        expense_data = {
            "name": "Stats Test",
            "amount": 50.0,
            "currency": "USD",
            "category_id": 1,
        }

        create_response = client.post("/expenses", json=expense_data)
        assert create_response.status_code == 201
        expense_id = create_response.json()["id"]

        # Check statistics after creation
        stats_response = client.get("/expenses/statistics")
        stats_after_create = stats_response.json()
        assert stats_after_create["total_expenses"] == 1
        assert stats_after_create["total_amount"] == 50.0

        # Update expense amount
        update_data = {"amount": 75.0}
        update_response = client.put(f"/expenses/{expense_id}", json=update_data)
        assert update_response.status_code == 200

        # Check statistics after update
        stats_response = client.get("/expenses/statistics")
        stats_after_update = stats_response.json()
        assert stats_after_update["total_expenses"] == 1
        assert stats_after_update["total_amount"] == 75.0

        # Delete expense
        delete_response = client.delete(f"/expenses/{expense_id}")
        assert delete_response.status_code == 204

        # Check statistics after deletion
        stats_response = client.get("/expenses/statistics")
        stats_after_delete = stats_response.json()
        assert stats_after_delete["total_expenses"] == 0
        assert stats_after_delete["total_amount"] == 0.0
