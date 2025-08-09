provider "aws" {
  region = var.region
}

resource "aws_instance" "test" {
  instance_type =var.instance_type
  ami = "ami-084568db4383264d4" # Example AMI, replace with a valid one  
}

resource "aws_s3_bucket" "example" {
  bucket = "terraform-streamlit-bucket-test-1128731"
}

data "aws_instances" "example" {
  instance_tags = {
    Environment = "Production"
  }

  instance_state_names = ["running", "stopped"]
}

resource "aws_eip" "test" {
  count = length(data.aws_instances.example.ids)
  instance = data.aws_instances.example.ids[count.index]
}