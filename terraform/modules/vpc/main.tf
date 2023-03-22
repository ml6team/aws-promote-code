data "aws_availability_zones" "available" {
  state = "available"
}

locals {
  dynamic_argument_list = [for i in range(var.availability_zones) : 4]

  list_of_list_of_cidr = [for cidr_block in cidrsubnets(var.vpc_cidr_block, 4, 4)
  : cidrsubnets(cidr_block, local.dynamic_argument_list...)]

  public_cidr_blocks  = local.list_of_list_of_cidr[0]
  private_cidr_blocks = local.list_of_list_of_cidr[1]
}

resource "aws_vpc" "main" {
  cidr_block = var.vpc_cidr_block
  tags = {
    Name   = var.network_name
    nimbus = "true"
  }
}

resource "aws_subnet" "private" {
  count = var.availability_zones

  vpc_id            = aws_vpc.main.id
  cidr_block        = local.private_cidr_blocks[count.index]
  availability_zone = data.aws_availability_zones.available.names[count.index]
  tags = {
    Name = "${var.private_prefix}-${var.subnetwork_name}-${count.index}"
  }
}

resource "aws_subnet" "public" {
  count = var.availability_zones

  vpc_id            = aws_vpc.main.id
  cidr_block        = local.public_cidr_blocks[count.index]
  availability_zone = data.aws_availability_zones.available.names[count.index]
  tags = {
    Name = "${var.public_prefix}-${var.subnetwork_name}-${count.index}"
  }
}

resource "aws_internet_gateway" "igw" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = var.network_name
  }
}

resource "aws_eip" "natip" {
  count = var.availability_zones

  vpc = true
}

resource "aws_nat_gateway" "nat" {
  count = var.availability_zones

  allocation_id = aws_eip.natip[count.index].id
  subnet_id     = aws_subnet.public[count.index].id
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.igw.id
  }
}

resource "aws_route_table" "private" {
  count = var.availability_zones

  vpc_id = aws_vpc.main.id
  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.nat[count.index].id
  }
}

resource "aws_route_table_association" "public" {
  count = var.availability_zones

  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table_association" "private" {
  count = var.availability_zones

  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private[count.index].id
}
