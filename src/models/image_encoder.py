"""Image encoder module based on a pretrained CNN backbone."""

from __future__ import annotations

import numpy as np
import torch
from torch import nn

try:
    from torchvision.models import ResNet50_Weights, resnet50
except ImportError:  # pragma: no cover - optional dependency
    ResNet50_Weights = None
    resnet50 = None


class ImageEncoder(nn.Module):
    """Extract compact visual embeddings from product images."""

    def __init__(self, model_name: str = 'resnet50', embedding_dim: int = 512, pretrained: bool = True, device: str = 'cpu'):
        super().__init__()
        self.model_name = model_name.lower()
        self.embedding_dim = embedding_dim
        self.device = device

        if self.model_name in {'resnet50', 'resnet'} and resnet50 is not None:
            weights = ResNet50_Weights.IMAGENET1K_V2 if pretrained else None
            backbone = resnet50(weights=weights)
            self.backbone = nn.Sequential(*list(backbone.children())[:-1])
            in_features = backbone.fc.in_features
            self.projection = nn.Linear(in_features, embedding_dim)
        else:
            self.backbone = nn.Sequential(
                nn.AdaptiveAvgPool2d((1, 1)),
                nn.Flatten(),
            )
            self.projection = nn.Linear(1, embedding_dim)

        self.to(self.device)

    def forward(self, images: torch.Tensor) -> torch.Tensor:
        if images.dim() == 3:
            images = images.unsqueeze(0)
        features = self.backbone(images.to(self.device))
        if features.dim() > 2:
            features = torch.flatten(features, start_dim=1)
        if isinstance(self.projection, nn.Linear):
            features = self.projection(features)
        return features

    def encode(self, images):
        """Return embeddings as a numpy array for downstream retrieval."""
        if isinstance(images, (list, tuple)) and images and isinstance(images[0], (np.ndarray, list)):
            images = np.stack([np.asarray(img) for img in images], axis=0)

        tensor = torch.as_tensor(images)
        if tensor.dtype != torch.float32:
            tensor = tensor.float()
        if tensor.ndim == 3:
            tensor = tensor.unsqueeze(0)
        with torch.no_grad():
            embeddings = self.forward(tensor)
        return embeddings.cpu().numpy()
