import os
import sys
import torch

from models import *
from datasets import *
from constants import PCAP_PATH

import torch.nn as nn
import torch.optim as optim

from torchvision import transforms
from torch.utils.data import DataLoader


def _train_one_epoch(model, criterion, optimizer, dataloader, epoch, args):
    """
    Train the model for one epoch
    """
    # Set the model to training mode
    model.train()

    for i, packets in enumerate(dataloader):
        running_loss = 0.0
        reshaped_packets = packets.reshape(args.batch_size, 1, model.input_dim, model.input_dim).to(torch.float)
        
        # Move the data to the device that is being used
        model = model.to(args.device)
        reshaped_packets = reshaped_packets.to(args.device)

        # Forward pass
        outputs = model(reshaped_packets)

        # Compute the loss: we're getting average loss over the batch here
        loss = criterion(outputs, reshaped_packets)

        # Backpropagation and optimization
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        running_loss += loss.item()

        # Print the loss and update the progress bar
        if (i + 1) % args.print_interval == 0:
            avg_loss = running_loss / args.print_interval
            print(f"Epoch {(i+1)}/ {(epoch+1)} Average Loss: {avg_loss}")

        # Calculate average loss for the epoch
        avg_epoch_loss = running_loss / (i+1)

        return avg_epoch_loss

def trainer(args):
    """
    Train the model using args provided by the user
    """
    # Create an instance of the model
    model = eval(args.model_name)()

    # Define loss function (Binary Cross-Entropy Loss for binary data)
    criterion = getattr(nn, args.loss)()

    # Define optimizer
    optimizer = getattr(optim, args.optimizer)(model.parameters(), lr=args.lr)
    
    # Define transformations (if needed)
    transform = transforms.Compose([
        # Add any desired transformations here
    ])

    best_loss = float('inf')
    best_model_state = None

    # Training loop
    for epoch in range(args.num_epochs):
        # Create the dataset
        dataset = eval(model.dataset)(pcap_file=args.traindata_file, max_iterations=sys.maxsize, transform=transform)

        # Create the DataLoader
        dataloader = DataLoader(dataset, batch_size=model.input_dim * args.batch_size, shuffle=False, drop_last=True)

        # Train the model for one epoch
        avg_epoch_loss = _train_one_epoch(model, criterion, optimizer, dataloader, epoch, args)

        # TODO: Add validation loop with early stopping here

        # Check if this is the best model so far
        if avg_epoch_loss < best_loss:
            best_loss = avg_epoch_loss
            print(f"BEST LOSS: {best_loss}")
            best_model_state = model.state_dict()

        print(f"Epoch {epoch+1} Average Loss: {avg_epoch_loss}")

    # Check if the folder exists, if not create it
    folder_path = f"../artifacts/models/{args.model_name}/"
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    # Define the file path for saving the best model
    # TODO: Add the epoch number to the file name and save an entire state dictionary
    file_path = os.path.join(folder_path, "model.pth")

    # Save the best trained model
    torch.save(best_model_state, file_path)
    print(f"Best average reconstruction error over the entire dataset: {best_loss}")
