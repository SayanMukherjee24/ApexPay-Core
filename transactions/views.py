# Django imports
from django.shortcuts import get_object_or_404

# App imports
from transactions.serializers import TransactionSerializer, WalletSerializer, StatusSerializer, TotalSerializer
from transactions.models import Transaction, Wallet
from accounts.models import User

# rest_framework imports
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated


class DepositView(GenericAPIView):
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        
        if serializer.is_valid():
            user = get_object_or_404(User, pk=request.user.pk)
            serializer.validated_data["user"] = user
            transaction_type = serializer.validated_data.get("transaction_type")
            amount = serializer.validated_data.get("amount")
            user_wallet = Wallet.objects.get(user=user)

            transaction_status = Transaction.objects.filter(user=user, transaction_type="deposit")
            last_tx = transaction_status.last()
            current_status = last_tx.status if last_tx else None

            if current_status == "pending":
                return Response(
                    {"message": "You have a pending transaction. Contact support."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if transaction_type == "deposit":
                user_wallet.available_amount += amount
                user_wallet.save()
                Transaction.objects.create(**serializer.validated_data)
                return Response({"message": "Transaction successful"}, status=status.HTTP_201_CREATED)

            return Response(
                {"message": "Invalid transaction type for deposit."},
                status=status.HTTP_400_BAD_REQUEST
            )


class WithdrawView(GenericAPIView):
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        
        if serializer.is_valid():
            user = get_object_or_404(User, pk=request.user.pk)
            serializer.validated_data["user"] = user
            transaction_type = serializer.validated_data.get("transaction_type")
            amount = serializer.validated_data.get("amount")
            user_wallet = Wallet.objects.get(user=user)

            transaction_status = Transaction.objects.filter(user=user, transaction_type="withdraw")
            last_tx = transaction_status.last()
            current_status = last_tx.status if last_tx else None

            if transaction_type != "withdraw":
                return Response(
                    {"message": "Invalid transaction type for withdraw."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if current_status == "pending":
                return Response(
                    {"message": "You have a pending transaction. Contact support."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if user_wallet.available_amount >= amount:
                user_wallet.available_amount -= amount
                user_wallet.save()
                Transaction.objects.create(**serializer.validated_data)
                return Response({"message": "Transaction successful"}, status=status.HTTP_201_CREATED)

            return Response(
                {"message": "Insufficient funds"},
                status=status.HTTP_400_BAD_REQUEST
            )


class GetTransactions(GenericAPIView):
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = get_object_or_404(User, pk=request.user.id)
        transactions = Transaction.objects.filter(user=user)
        serializer = self.serializer_class(instance=transactions, many=True)
        
        return Response(
            {"message": "Your transactions are below", "data": serializer.data},
            status=status.HTTP_200_OK
        )


class GetWallet(GenericAPIView):
    serializer_class = WalletSerializer
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = get_object_or_404(User, pk=request.user.id)
        balance = Wallet.objects.filter(user=user)
        serializer = self.serializer_class(instance=balance, many=True)
        
        return Response(
            {"message": "Balance retrieved", "data": serializer.data},
            status=status.HTTP_200_OK
        )


class GetDepositStatus(GenericAPIView):
    serializer_class = StatusSerializer
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = get_object_or_404(User, pk=request.user.id)
        transaction_status = Transaction.objects.filter(user=user, transaction_type="deposit")
        last_tx = transaction_status.last()
        current_status = last_tx.status if last_tx else None
        serializer = self.serializer_class(instance=transaction_status, many=True)

        if not current_status:
            return Response({"message": "You have no transaction records yet"}, status=status.HTTP_200_OK)

        messages = {
            "pending": "Your deposit is pending",
            "processing": "Your deposit is processing",
            "processed": "Your deposit is completed",
        }

        return Response(
            {"message": messages.get(current_status, "No records"), "data": serializer.data},
            status=status.HTTP_200_OK
        )


class GetWithdrawStatus(GenericAPIView):
    serializer_class = StatusSerializer
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = get_object_or_404(User, pk=request.user.id)
        transaction_status = Transaction.objects.filter(user=user, transaction_type="withdraw")
        last_tx = transaction_status.last()
        current_status = last_tx.status if last_tx else None
        serializer = self.serializer_class(instance=transaction_status, many=True)

        if not current_status:
            return Response({"message": "You have no transaction records yet"}, status=status.HTTP_200_OK)

        messages = {
            "pending": "Your withdrawal is pending",
            "processing": "Your withdrawal is processing",
            "processed": "Your withdrawal is completed",
        }

        return Response(
            {"message": messages.get(current_status, "No records"), "data": serializer.data},
            status=status.HTTP_200_OK
        )


class TotalDeposit(GenericAPIView):
    serializer_class = TotalSerializer
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = get_object_or_404(User, pk=request.user.id)
        total_deposit = Transaction.objects.filter(
            user=user, transaction_type="deposit", status="processed"
        )
        serializer = self.serializer_class(instance=total_deposit, many=True)

        if total_deposit.count() == 0:
            return Response({"message": "You have no transaction records yet"}, status=status.HTTP_200_OK)

        return Response(
            {"message": "Total deposit amount", "data": serializer.data},
            status=status.HTTP_200_OK
        )


class TotalWithdraw(GenericAPIView):
    serializer_class = TotalSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = get_object_or_404(User, pk=request.user.id)
        total_withdraw = Transaction.objects.filter(
            user=user, transaction_type="withdraw", status="processed"
        )
        serializer = self.serializer_class(instance=total_withdraw, many=True)

        if total_withdraw.count() == 0:
            return Response({"message": "You have no transaction records yet"}, status=status.HTTP_200_OK)

        return Response(
            {"message": "Total withdraw amount", "data": serializer.data},
            status=status.HTTP_200_OK
        )
