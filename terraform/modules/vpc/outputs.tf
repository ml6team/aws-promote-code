output "network_id" {
  value = aws_vpc.main.id
}

output "public_subnetwork_id" {
  value = aws_subnet.public[0].id
}
