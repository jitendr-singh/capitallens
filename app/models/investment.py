from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from app.config.database import Base
import enum

class InvestmentStatus(str, enum.Enum):
    active = "active"
    redeemed = "redeemed"

class Investment(Base):
    __tablename__ = "investments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    asset_name = Column(String(255), nullable=False)
    asset_type = Column(String(50), nullable=False) # 'stocks', 'fixed_deposit', 'mutual_funds', 'gold', 'govt_schemes', 'real_estate'
    
    amount_invested = Column(Float, nullable=False)
    current_value = Column(Float, nullable=False)
    
    # Specific fields
    quantity = Column(Float, nullable=True) # shares, units, grams
    buy_price = Column(Float, nullable=True) # buy price or NAV
    
    interest_rate = Column(Float, nullable=True) # FD interest / Gov returns
    maturity_date = Column(DateTime, nullable=True) # FD maturity
    
    annual_contribution = Column(Float, nullable=True) # PPF/NPS
    rental_income = Column(Float, nullable=True) # Real Estate
    appreciation_rate = Column(Float, nullable=True) # Real Estate / Gold growth
    
    status = Column(Enum(InvestmentStatus), default=InvestmentStatus.active, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship with User
    user = relationship("User", back_populates="investments")

    def __repr__(self):
        return f"<Investment(id={self.id}, type={self.asset_type}, name={self.asset_name})>"
