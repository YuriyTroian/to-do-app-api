variable "cache_enabled" {
  description = "Увімкнути cache-aside для GET /tasks/"
  type        = bool
  default     = true
}

resource "aws_security_group" "redis_sg" {
  name        = "todo-redis-sg"
  description = "Redis only from ECS tasks"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs_sg.id]
  }
}

resource "aws_elasticache_subnet_group" "redis" {
  name       = "todo-redis-subnets"
  subnet_ids = data.aws_subnets.default.ids
}

resource "aws_elasticache_cluster" "redis" {
  cluster_id         = "todo-redis"
  engine             = "redis"
  node_type          = "cache.t4g.micro"
  num_cache_nodes    = 1
  port               = 6379
  subnet_group_name  = aws_elasticache_subnet_group.redis.name
  security_group_ids = [aws_security_group.redis_sg.id]
}

output "redis_endpoint" {
  value = aws_elasticache_cluster.redis.cache_nodes[0].address
}
